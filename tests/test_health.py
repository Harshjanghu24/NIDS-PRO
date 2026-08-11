import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_version_endpoint(async_client: AsyncClient):
    response = await async_client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0-DRAFT"


@pytest.mark.asyncio
async def test_api_v2_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_v2_ready_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v2/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
