"""Tests for Flask core application initialization and routing."""

def test_index_route(client):
    """Test that GET / returns HTTP 200 and renders the upload HTML interface."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Network Intrusion Detection System" in response.data or b"<!DOCTYPE html>" in response.data

def test_404_custom_handler(client):
    """Test that accessing an undefined route returns 404 JSON response."""
    response = client.get("/nonexistent-endpoint-12345")
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data is not None
    assert json_data.get("status") == "error"
    assert "not found" in json_data.get("message", "").lower()
