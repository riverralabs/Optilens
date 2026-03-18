"""Tests for root and health check endpoints."""


def test_root_returns_service_info(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "optilens-api"
    assert data["version"] == "0.1.0"
    assert "docs" in data


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "optilens-api"
