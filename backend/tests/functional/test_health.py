"""
Functional tests for the health endpoint.
"""
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
