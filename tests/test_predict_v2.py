"""
Phase E — ML Engine Tests.

Tests cover: single prediction (valid/missing features), batch prediction
(valid CSV, missing columns, no file), history retrieval, and auth/role
enforcement on all three endpoints (401 without token, 403 with wrong role).
"""

import io
import os
import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_current_user, require_role
from app.api.v2.schemas.prediction import NSL_KDD_FEATURES
from app.core.database import Base, get_db_session
from app.core.security import create_access_token, hash_password
from app.infrastructure.repositories.models import User
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.main import app
from app.services.model_loader import LoadedModel, _loaded


# ── Fake model artifacts for testing ──

def _build_fake_model():
    """Create a fake model + preprocessor + label_encoder mimicking XGBoost."""
    classes = np.array(["DOS", "Normal", "PROBE", "R2L", "U2R"])

    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.05, 0.80, 0.05, 0.05, 0.05]])
    model.classes_ = classes
    # For SHAP: TreeExplainer needs a real-ish predict, but we'll mock SHAP entirely
    model.predict.return_value = np.array([1])

    preprocessor = MagicMock()
    preprocessor.transform.return_value = np.zeros((1, 122))
    preprocessor.get_feature_names_out.return_value = [f"feat_{i}" for i in range(122)]

    label_encoder = MagicMock()
    label_encoder.classes_ = classes
    label_encoder.inverse_transform.side_effect = lambda x: classes[x]

    return model, preprocessor, label_encoder


def _build_fake_model_batch(n_rows):
    """Create fake model that handles batch predictions."""
    classes = np.array(["DOS", "Normal", "PROBE", "R2L", "U2R"])

    model = MagicMock()
    # Return varying probas for realism
    probas = np.tile([0.05, 0.80, 0.05, 0.05, 0.05], (n_rows, 1))
    model.predict_proba.return_value = probas
    model.classes_ = classes

    preprocessor = MagicMock()
    preprocessor.transform.return_value = np.zeros((n_rows, 122))

    label_encoder = MagicMock()
    label_encoder.classes_ = classes
    label_encoder.inverse_transform.side_effect = lambda x: classes[x]

    return model, preprocessor, label_encoder


# ── Sample input data ──

def _sample_features() -> dict:
    """Return a valid 41-feature dictionary for a single prediction."""
    features = {}
    for f in NSL_KDD_FEATURES:
        if f in ("protocol_type", "service", "flag"):
            features[f] = "tcp" if f == "protocol_type" else ("http" if f == "service" else "SF")
        else:
            features[f] = 0
    return features


def _sample_csv_content(n_rows: int = 3) -> str:
    """Return a valid CSV string with the 41 expected columns."""
    header = ",".join(NSL_KDD_FEATURES)
    rows = []
    for _ in range(n_rows):
        vals = []
        for f in NSL_KDD_FEATURES:
            if f in ("protocol_type",):
                vals.append("tcp")
            elif f == "service":
                vals.append("http")
            elif f == "flag":
                vals.append("SF")
            else:
                vals.append("0")
        rows.append(",".join(vals))
    return header + "\n" + "\n".join(rows)


# ── Fixtures ──


@pytest_asyncio.fixture
async def predict_db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def predict_db_session(predict_db_engine):
    factory = async_sessionmaker(bind=predict_db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def analyst_user(predict_db_session: AsyncSession):
    """Seed a user with ANALYST role."""
    role_repo = RoleRepository(predict_db_session)
    user_repo = UserRepository(predict_db_session)
    role = await role_repo.create(role_name="ANALYST", description="SOC Analyst")
    user = await user_repo.create(
        username="analyst_e", email="analyst_e@test.com",
        password_hash=hash_password("TestP@ss1"),
    )
    await user_repo.assign_role(user, role)
    await predict_db_session.commit()
    return user


@pytest_asyncio.fixture
async def viewer_user(predict_db_session: AsyncSession):
    """Seed a user with VIEWER role (should be denied)."""
    role_repo = RoleRepository(predict_db_session)
    user_repo = UserRepository(predict_db_session)
    role = await role_repo.create(role_name="VIEWER", description="Read-only")
    user = await user_repo.create(
        username="viewer_e", email="viewer_e@test.com",
        password_hash=hash_password("TestP@ss1"),
    )
    await user_repo.assign_role(user, role)
    await predict_db_session.commit()
    return user


@pytest_asyncio.fixture
async def predict_client(predict_db_session: AsyncSession):
    """HTTPX client wired to in-memory SQLite."""
    async def _override_db():
        yield predict_db_session

    app.dependency_overrides[get_db_session] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


def _inject_fake_model():
    """Inject fake model artifacts into the module-level singleton."""
    model, preprocessor, label_encoder = _build_fake_model()
    _loaded.model = model
    _loaded.preprocessor = preprocessor
    _loaded.label_encoder = label_encoder
    _loaded.model_id = uuid.uuid4()
    _loaded.class_names = ["DOS", "Normal", "PROBE", "R2L", "U2R"]


def _inject_fake_model_batch(n_rows):
    """Inject fake model for batch with n_rows."""
    model, preprocessor, label_encoder = _build_fake_model_batch(n_rows)
    _loaded.model = model
    _loaded.preprocessor = preprocessor
    _loaded.label_encoder = label_encoder
    _loaded.model_id = uuid.uuid4()
    _loaded.class_names = ["DOS", "Normal", "PROBE", "R2L", "U2R"]


def _make_token(user: User, roles: list[str]) -> str:
    return create_access_token(subject=str(user.id), extra_claims={"roles": roles})


# ── Auth enforcement tests ──


@pytest.mark.asyncio
async def test_predict_401_no_token(predict_client: AsyncClient):
    """POST /predict returns 401 without a Bearer token."""
    resp = await predict_client.post("/api/v2/predict", json={"features": {}})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_predict_batch_401_no_token(predict_client: AsyncClient):
    """POST /predict/batch returns 401 without a Bearer token."""
    resp = await predict_client.post("/api/v2/predict/batch")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_predict_history_401_no_token(predict_client: AsyncClient):
    """GET /predict/history returns 401 without a Bearer token."""
    resp = await predict_client.get("/api/v2/predict/history")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_predict_403_viewer_role(predict_client: AsyncClient, viewer_user: User):
    """POST /predict returns 403 for VIEWER role."""
    token = _make_token(viewer_user, ["VIEWER"])
    _inject_fake_model()
    resp = await predict_client.post(
        "/api/v2/predict",
        json={"features": _sample_features()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_predict_batch_403_viewer_role(predict_client: AsyncClient, viewer_user: User):
    """POST /predict/batch returns 403 for VIEWER role."""
    token = _make_token(viewer_user, ["VIEWER"])
    csv_content = _sample_csv_content(1)
    resp = await predict_client.post(
        "/api/v2/predict/batch",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.csv", csv_content.encode(), "text/csv")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_predict_history_403_viewer_role(predict_client: AsyncClient, viewer_user: User):
    """GET /predict/history returns 403 for VIEWER role."""
    token = _make_token(viewer_user, ["VIEWER"])
    resp = await predict_client.get(
        "/api/v2/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── Single prediction tests ──


@pytest.mark.asyncio
@patch("app.api.v2.predict._compute_shap_top", return_value=[])
async def test_predict_single_valid(mock_shap, predict_client: AsyncClient, analyst_user: User):
    """POST /predict with valid 41-feature input returns a prediction."""
    _inject_fake_model()
    token = _make_token(analyst_user, ["ANALYST"])
    features = _sample_features()

    resp = await predict_client.post(
        "/api/v2/predict",
        json={"features": features},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["predicted_category"] == "Normal"
    assert "confidence_scores" in data
    assert len(data["confidence_scores"]) == 5
    assert data["inference_latency_ms"] >= 0


@pytest.mark.asyncio
@patch("app.api.v2.predict._compute_shap_top", return_value=[])
async def test_predict_single_missing_features(mock_shap, predict_client: AsyncClient, analyst_user: User):
    """POST /predict with missing features returns 422."""
    _inject_fake_model()
    token = _make_token(analyst_user, ["ANALYST"])
    # Only send partial features
    features = {"duration": 0, "protocol_type": "tcp"}

    resp = await predict_client.post(
        "/api/v2/predict",
        json={"features": features},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert "Missing required features" in resp.json()["detail"]


# ── Batch prediction tests ──


@pytest.mark.asyncio
async def test_predict_batch_valid(predict_client: AsyncClient, analyst_user: User):
    """POST /predict/batch with valid CSV returns predictions and summary."""
    n_rows = 3
    _inject_fake_model_batch(n_rows)
    token = _make_token(analyst_user, ["ANALYST"])
    csv_content = _sample_csv_content(n_rows)

    resp = await predict_client.post(
        "/api/v2/predict/batch",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.csv", csv_content.encode(), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == n_rows
    assert len(data["predictions"]) == n_rows
    assert "Normal" in data["summary"]
    assert data["summary"]["Normal"]["count"] == n_rows


@pytest.mark.asyncio
async def test_predict_batch_missing_columns(predict_client: AsyncClient, analyst_user: User):
    """POST /predict/batch with CSV missing required columns returns 400."""
    _inject_fake_model()
    token = _make_token(analyst_user, ["ANALYST"])
    # CSV with only 2 columns
    csv_content = "duration,protocol_type\n0,tcp\n"

    resp = await predict_client.post(
        "/api/v2/predict/batch",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.csv", csv_content.encode(), "text/csv")},
    )
    assert resp.status_code == 400
    assert "Missing required columns" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_predict_batch_no_file(predict_client: AsyncClient, analyst_user: User):
    """POST /predict/batch without a file returns 422."""
    token = _make_token(analyst_user, ["ANALYST"])

    resp = await predict_client.post(
        "/api/v2/predict/batch",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ── History retrieval test ──


@pytest.mark.asyncio
@patch("app.api.v2.predict._compute_shap_top", return_value=[])
async def test_predict_history_retrieval(mock_shap, predict_client: AsyncClient, analyst_user: User):
    """GET /predict/history returns persisted predictions."""
    _inject_fake_model()
    token = _make_token(analyst_user, ["ANALYST"])
    features = _sample_features()

    # Create a prediction first
    await predict_client.post(
        "/api/v2/predict",
        json={"features": features},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Retrieve history
    resp = await predict_client.get(
        "/api/v2/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["predicted_category"] == "Normal"
