"""Prediction API endpoints for V2.

POST /api/v2/predict       — single-flow prediction with SHAP explanation
POST /api/v2/predict/batch — CSV upload batch prediction
GET  /api/v2/predict/history — paginated prediction history for the user
"""

import io
import time

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_current_user,
    get_prediction_repository,
)
from app.api.v2.schemas.prediction import (
    NSL_KDD_FEATURES,
    BatchPredictionResponse,
    BatchRowPrediction,
    CategoryCount,
    FlowHistoryItem,
    PredictRequest,
    PredictionHistoryResponse,
    ShapContribution,
    SinglePredictionResponse,
)
from app.infrastructure.repositories.models import User
from app.infrastructure.repositories.prediction_repository import PredictionRepository
from app.services.model_loader import LoadedModel, get_loaded_model

router = APIRouter(prefix="/predict", tags=["Predictions"])


def _require_analyst_or_admin():
    """Dependency: user must have ANALYST or ADMIN role."""
    async def _check(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_roles = {r.role_name for r in current_user.roles}
        if not user_roles & {"ANALYST", "ADMIN"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ANALYST or ADMIN role required",
            )
        return current_user

    return _check


def _run_inference(lm: LoadedModel, df: pd.DataFrame):
    """Transform features and run model prediction. Returns (predictions, probabilities)."""
    X = lm.preprocessor.transform(df)
    probas = lm.model.predict_proba(X)
    pred_indices = np.argmax(probas, axis=1)

    if lm.label_encoder is not None:
        pred_labels = lm.label_encoder.inverse_transform(pred_indices)
    else:
        pred_labels = lm.model.classes_[pred_indices]

    return pred_labels, probas


def _compute_shap_top(lm: LoadedModel, df: pd.DataFrame, top_n: int = 5) -> list[ShapContribution]:
    """Compute SHAP values for a single row and return the top contributors."""
    try:
        import shap
    except ImportError:
        return []

    X = lm.preprocessor.transform(df)

    explainer = shap.TreeExplainer(lm.model)
    shap_values = explainer.shap_values(X)

    # shap_values is a list of arrays (one per class) for multi-class
    # Pick the predicted class's SHAP values
    pred_idx = int(np.argmax(lm.model.predict_proba(X)[0]))

    if isinstance(shap_values, list):
        sv = shap_values[pred_idx][0]
    else:
        # Single array for binary or newer SHAP output
        sv = shap_values[0]

    # Build feature names from the preprocessor
    feature_names = _get_transformed_feature_names(lm)
    if len(feature_names) != len(sv):
        # Fallback: generic names
        feature_names = [f"feature_{i}" for i in range(len(sv))]

    # Sort by absolute SHAP value
    indices = np.argsort(np.abs(sv))[::-1][:top_n]
    return [
        ShapContribution(feature=feature_names[i], value=round(float(sv[i]), 6))
        for i in indices
    ]


def _get_transformed_feature_names(lm: LoadedModel) -> list[str]:
    """Extract feature names from the fitted ColumnTransformer."""
    try:
        return list(lm.preprocessor.get_feature_names_out())
    except Exception:
        return []


# ── POST /predict ──


@router.post(
    "",
    response_model=SinglePredictionResponse,
    summary="Single-flow prediction with SHAP explainability",
)
async def predict_single(
    body: PredictRequest,
    current_user: User = Depends(_require_analyst_or_admin()),
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
):
    lm = get_loaded_model()

    # Validate all 41 features present
    missing = [f for f in NSL_KDD_FEATURES if f not in body.features]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required features: {missing}",
        )

    df = pd.DataFrame([body.features])[NSL_KDD_FEATURES]

    t0 = time.perf_counter()
    pred_labels, probas = _run_inference(lm, df)
    latency_ms = (time.perf_counter() - t0) * 1000

    predicted_category = str(pred_labels[0])
    confidence_scores = {
        cls: round(float(p), 6) for cls, p in zip(lm.class_names, probas[0])
    }
    max_confidence = float(max(probas[0]))

    # SHAP explanation (single prediction only)
    shap_top = _compute_shap_top(lm, df)

    # Persist to flow_history
    protocol = body.features.get("protocol_type")
    await pred_repo.create_flow(
        raw_41_features=dict(body.features),
        predicted_category=predicted_category,
        confidence_score=max_confidence,
        inference_latency_ms=round(latency_ms, 2),
        protocol_type=str(protocol) if protocol else None,
        model_id=lm.model_id,
    )

    return SinglePredictionResponse(
        predicted_category=predicted_category,
        confidence_scores=confidence_scores,
        shap_top_features=shap_top,
        inference_latency_ms=round(latency_ms, 2),
    )


# ── POST /predict/batch ──


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Batch prediction from CSV file upload",
)
async def predict_batch(
    file: UploadFile = File(...),
    current_user: User = Depends(_require_analyst_or_admin()),
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
):
    if file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    lm = get_loaded_model()

    # Read CSV
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse CSV file")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Validate all 41 columns present
    missing = [c for c in NSL_KDD_FEATURES if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}",
        )

    df = df[NSL_KDD_FEATURES]

    t0 = time.perf_counter()
    pred_labels, probas = _run_inference(lm, df)
    latency_ms = (time.perf_counter() - t0) * 1000

    # Build per-row predictions and persist each flow
    predictions = []
    for idx in range(len(pred_labels)):
        cat = str(pred_labels[idx])
        conf = float(np.max(probas[idx]))
        predictions.append(BatchRowPrediction(row=idx, predicted_category=cat, confidence_score=round(conf, 6)))

        row_features = df.iloc[idx].to_dict()
        protocol = row_features.get("protocol_type")
        await pred_repo.create_flow(
            raw_41_features=row_features,
            predicted_category=cat,
            confidence_score=conf,
            inference_latency_ms=round(latency_ms / len(pred_labels), 2),
            protocol_type=str(protocol) if protocol else None,
            model_id=lm.model_id,
        )

    # Summary counts
    total = len(pred_labels)
    counts: dict[str, int] = {}
    for p in predictions:
        counts[p.predicted_category] = counts.get(p.predicted_category, 0) + 1

    summary = {
        cat: CategoryCount(count=cnt, percentage=round(cnt / total * 100, 2))
        for cat, cnt in sorted(counts.items())
    }

    return BatchPredictionResponse(
        total_rows=total,
        summary=summary,
        predictions=predictions,
        inference_latency_ms=round(latency_ms, 2),
    )


# ── GET /predict/history ──


@router.get(
    "/history",
    response_model=PredictionHistoryResponse,
    summary="Paginated prediction history for authenticated user",
)
async def predict_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(_require_analyst_or_admin()),
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    skip = (page - 1) * page_size
    flows = await pred_repo.list(skip=skip, limit=page_size)
    total = await pred_repo.count()

    items = []
    for f in flows:
        items.append(FlowHistoryItem(
            id=f.id,
            captured_at=f.captured_at.isoformat() if f.captured_at else "",
            predicted_category=f.predicted_category,
            confidence_score=f.confidence_score,
            inference_latency_ms=f.inference_latency_ms,
            protocol_type=f.protocol_type,
        ))

    return PredictionHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
