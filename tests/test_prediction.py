"""Tests for valid prediction flow via POST /predict."""

import io

def test_predict_valid_csv(client, sample_csv_bytes):
    """Test POST /predict with sample_upload.csv returns 200 OK and expected structure."""
    data = {
        "file": (io.BytesIO(sample_csv_bytes), "sample_upload.csv")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 200

    json_data = response.get_json()
    assert json_data is not None
    assert "summary" in json_data
    assert "predictions" in json_data

    predictions = json_data["predictions"]
    assert len(predictions) == 20
    assert "predicted_category" in predictions[0]

def test_predict_single_row_csv(client, valid_csv_stream):
    """Test POST /predict with a single row CSV stream."""
    data = {
        "file": (io.BytesIO(valid_csv_stream), "single_row.csv")
    }
    response = client.post("/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 200

    json_data = response.get_json()
    assert json_data is not None
    assert len(json_data["predictions"]) == 1
    assert json_data["predictions"][0]["predicted_category"] in ("Normal", "DOS", "PROBE", "R2L", "U2R")
