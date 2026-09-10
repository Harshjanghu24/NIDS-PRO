import redis.asyncio as aioredis
from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal, redis_client
from app.core.logging import logger

router = APIRouter(tags=["Health & System Diagnostics"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class ServiceStatus(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    database: ServiceStatus
    redis: ServiceStatus


class VersionResponse(BaseModel):
    version: str
    app_name: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check"
)
async def get_health() -> HealthResponse:
    """
    Returns basic application health status for container liveness probes.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Dependency Readiness Check"
)
async def get_readiness() -> ReadinessResponse:
    """
    Verifies connectivity to PostgreSQL database and Redis memory broker.
    """
    import time

    # Check Database Connectivity
    db_status = ServiceStatus(status="unknown")
    start_time = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        db_status = ServiceStatus(status="healthy", latency_ms=round(latency, 2))
    except Exception as exc:
        logger.warning("readiness_db_check_failed", error=str(exc))
        db_status = ServiceStatus(status="unhealthy", error=str(exc))

    # Check Redis Connectivity
    redis_status = ServiceStatus(status="unknown")
    start_time = time.perf_counter()
    try:
        if redis_client is not None:
            await redis_client.ping()
            latency = (time.perf_counter() - start_time) * 1000
            redis_status = ServiceStatus(status="healthy", latency_ms=round(latency, 2))
        else:
            # Try ad-hoc ping if pool is not yet bound
            temp_redis = aioredis.from_url(settings.REDIS_URL)
            await temp_redis.ping()
            await temp_redis.close()
            latency = (time.perf_counter() - start_time) * 1000
            redis_status = ServiceStatus(status="healthy", latency_ms=round(latency, 2))
    except Exception as exc:
        logger.warning("readiness_redis_check_failed", error=str(exc))
        redis_status = ServiceStatus(status="unhealthy", error=str(exc))

    overall_status = "ready" if (db_status.status == "healthy" and redis_status.status == "healthy") else "degraded"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status
    )


@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="System Version Information"
)
async def get_version() -> VersionResponse:
    """
    Returns system build version and active configuration metadata.
    """
    return VersionResponse(
        version=settings.APP_VERSION,
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT
    )
