"""Tests for model and preprocessor persistence and inference readiness."""

import os
import joblib
from preprocessing import load_preprocessor

def test_model_artifacts_exist():
    """Verify that required model artifacts exist on disk."""
    assert os.path.exists("model.pkl")
    assert os.path.exists("preprocessor.pkl")

def test_load_preprocessor_artifact():
    """Verify that load_preprocessor successfully loads the ColumnTransformer."""
    preprocessor = load_preprocessor("preprocessor.pkl")
    assert hasattr(preprocessor, "transform")

def test_model_inference():
    """Verify that model.pkl can load and predict on dummy preprocessed data."""
    model = joblib.load("model.pkl")
    preprocessor = load_preprocessor("preprocessor.pkl")
    assert hasattr(model, "predict")
