import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v2.health import router as health_router
from app.api.v2.router import api_v2_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_redis_pool, init_redis_pool
from app.core.logging import logger
from app.core.rate_limit import LoginRateLimitMiddleware
from app.services.model_loader import load_active_model, register_v1_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI Lifespan Async Context Manager handling system startup and shutdown events.
    """
    # Startup Events
    logger.info(
        "app_startup_begin",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )
    try:
        await init_redis_pool()

        # Register V1 model artifacts and load into memory
        async with AsyncSessionLocal() as session:
            await register_v1_model(session)
            await session.commit()
        async with AsyncSessionLocal() as session:
            await load_active_model(session)

        logger.info("app_startup_complete")
    except Exception as exc:
        logger.error("app_startup_failed", error=str(exc))

    yield

    # Shutdown Events
    logger.info("app_shutdown_begin")
    try:
        await close_redis_pool()
        logger.info("app_shutdown_complete")
    except Exception as exc:
        logger.error("app_shutdown_failed", error=str(exc))


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI-Powered Network Intrusion Detection Platform API",
    openapi_url="/api/v2/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Login Rate Limiter (must be added after CORS so CORS headers are applied)
app.add_middleware(LoginRateLimitMiddleware)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        correlation_id=correlation_id
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://api.nids.local/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please contact the administrator.",
            "correlation_id": correlation_id
        }
    )


# Include Top-Level Diagnostic Routes (Supports /health, /ready, /version)
app.include_router(health_router)

# Include API v2 Routers
app.include_router(api_v2_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
