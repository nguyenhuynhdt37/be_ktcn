import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Tests that the root-level health endpoint functions correctly and returns 200.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "healthy"
    assert data["details"]["postgres"] == "healthy"
    assert data["details"]["redis"] == "healthy"


@pytest.mark.asyncio
async def test_404_error_envelope(client: AsyncClient):
    """
    Tests that unmatched paths return the standard JSON error envelope.
    """
    response = await client.get("/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
