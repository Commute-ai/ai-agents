from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the root health endpoint"""
    response = client.get("/api/v1/health/health")
    assert response.status_code == 200
    assert "OK" in response.text
