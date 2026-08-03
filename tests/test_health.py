"""Tests for the /health endpoint used by container orchestrators."""

def test_health_check_endpoint(client):
    """Test that GET /health returns 200 OK with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {"status": "ok"}
