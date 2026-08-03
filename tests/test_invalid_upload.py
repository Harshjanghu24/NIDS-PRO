"""Tests for invalid upload handling and input validation in POST /predict."""

import io

def test_predict_no_file(client):
    """Test POST /predict without a file parameter returns 400 Bad Request."""
    response = client.post("/predict", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data.get("status") == "error"
    assert "no file" in json_data.get("message", "").lower()

def test_predict_empty_filename(client):
    """Test POST /predict with empty filename returns 400 Bad Request."""
    data = {
        "file": (io.BytesIO(b""), "")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data.get("status") == "error"

def test_predict_missing_columns(client, missing_cols_csv_bytes):
    """Test POST /predict with missing NSL-KDD columns returns 400 Bad Request."""
    data = {
        "file": (io.BytesIO(missing_cols_csv_bytes), "invalid_headers.csv")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data.get("status") == "error"
    assert "missing" in json_data.get("message", "").lower()
    assert "missing_columns" in json_data

def test_predict_malformed_utf8(client, malformed_csv_bytes):
    """Test POST /predict with invalid non-UTF8 bytes returns 400 Bad Request."""
    data = {
        "file": (io.BytesIO(malformed_csv_bytes), "corrupted.csv")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data.get("status") == "error"
    assert "failed to parse" in json_data.get("message", "").lower()

def test_predict_file_too_large(client):
    """Test POST /predict with a payload exceeding 5 MB returns 413 Payload Too Large."""
    large_content = b"a" * (5 * 1024 * 1024 + 1024)
    data = {
        "file": (io.BytesIO(large_content), "large.csv")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 413
    json_data = response.get_json()
    assert json_data.get("status") == "error"
    assert "file too large" in json_data.get("message", "").lower()
