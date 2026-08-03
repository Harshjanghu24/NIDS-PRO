"""Pytest configuration and shared fixtures for the NIDS test suite."""

import io
import os
import sys
import pytest

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from preprocessing import load_column_names

@pytest.fixture
def app():
    """Provide Flask app instance configured for testing."""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture
def client(app):
    """Provide Flask test client."""
    return app.test_client()

@pytest.fixture
def sample_csv_bytes():
    """Read sample_upload.csv content for testing prediction upload."""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_upload.csv")
    with open(filepath, "rb") as f:
        return f.read()

@pytest.fixture
def valid_csv_stream():
    """Create a StringIO stream with valid header + 1 sample row."""
    cols = load_column_names()
    feature_cols = [c for c in cols if c not in ("attack_type", "difficulty_level")]
    header = ",".join(feature_cols) + "\n"
    # Row matching 41 columns
    row = "0,tcp,http,SF,181,5450,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,8,8,0.0,0.0,0.0,0.0,1.0,0.0,0.0,9,9,1.0,0.0,0.11,0.0,0.0,0.0,0.0,0.0\n"
    return (header + row).encode("utf-8")

@pytest.fixture
def missing_cols_csv_bytes():
    """CSV missing required feature columns."""
    return b"duration,protocol_type\n0,tcp\n"

@pytest.fixture
def malformed_csv_bytes():
    """Corrupted non-UTF8 bytes to trigger parser error."""
    return b"\x80\x81\x82\x83\xff\xfe"
