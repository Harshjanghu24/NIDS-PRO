"""Model loader service — loads the active model's artifacts into memory once.

On startup, register_v1_model() inserts the V1 model into the models table
(if not already present) and marks it active. load_active_model() then reads
the artifact path from ModelRepository.get_active_model() and deserializes
the three pickle files (model, preprocessor, label_encoder) into a singleton
that the prediction endpoints consume.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import joblib
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.infrastructure.repositories.model_repository import ModelRepository


@dataclass
class LoadedModel:
    """In-memory container for the deserialized model artifacts."""
    model: Any = None
    preprocessor: Any = None
    label_encoder: Any = None
    model_id: Optional[Any] = None  # uuid from the DB
    class_names: list[str] = field(default_factory=list)


# Module-level singleton — populated once on startup
_loaded: LoadedModel = LoadedModel()


def get_loaded_model() -> LoadedModel:
    """Return the in-memory model singleton. Raises if not yet loaded."""
    if _loaded.model is None:
        raise RuntimeError("Model artifacts not loaded — call load_active_model() first")
    return _loaded


# Default artifact directory (relative to project root inside the container)
_ARTIFACT_DIR = os.environ.get("MODEL_ARTIFACT_DIR", ".")


async def register_v1_model(session: AsyncSession) -> None:
    """Register the V1 XGBoost model artifacts in the models table if not present."""
    repo = ModelRepository(session)
    existing = await repo.get_by_version("v1.0.0")
    if existing is not None:
        logger.info("model_registry_v1_exists", model_id=str(existing.id))
        # Ensure it's active
        if not existing.is_active:
            await repo.set_active_model(existing.id)
        return

    model = await repo.create(
        model_name="XGBoost NSL-KDD Classifier",
        version="v1.0.0",
        model_type="XGBOOST",
        artifact_path=_ARTIFACT_DIR,
        is_active=True,
        validation_metrics={"source": "train_model.py", "dataset": "NSL-KDD"},
    )
    logger.info("model_registry_v1_registered", model_id=str(model.id))


async def load_active_model(session: AsyncSession) -> LoadedModel:
    """Load the active model's artifacts from disk into the module singleton."""
    global _loaded

    repo = ModelRepository(session)
    active = await repo.get_active_model()
    if active is None:
        raise RuntimeError("No active model found in the database")

    artifact_dir = active.artifact_path
    model_path = os.path.join(artifact_dir, "model.pkl")
    preprocessor_path = os.path.join(artifact_dir, "preprocessor.pkl")
    label_encoder_path = os.path.join(artifact_dir, "label_encoder.pkl")

    _loaded.model = joblib.load(model_path)
    _loaded.preprocessor = joblib.load(preprocessor_path)
    _loaded.label_encoder = joblib.load(label_encoder_path)
    _loaded.model_id = active.id

    # Derive class names from the label encoder
    if _loaded.label_encoder is not None and hasattr(_loaded.label_encoder, "classes_"):
        _loaded.class_names = [str(c) for c in _loaded.label_encoder.classes_]
    else:
        # Fallback: the model predicts string labels directly
        _loaded.class_names = ["DOS", "Normal", "PROBE", "R2L", "U2R"]

    logger.info(
        "model_loaded",
        model_id=str(active.id),
        version=active.version,
        classes=_loaded.class_names,
    )
    return _loaded
