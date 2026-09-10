from __future__ import annotations

from typing import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

# SQLAlchemy 2.0 Declarative Base for future entities
Base = declarative_base()

# Async SQLAlchemy Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redis Client Instance (Initialized on app startup)
redis_client: aioredis.Redis | None = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for acquiring an async database session per request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("database_session_rollback", error=str(exc))
            raise exc


async def init_redis_pool() -> aioredis.Redis:
    """
    Initializes and returns the global Redis async client.
    """
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("redis_pool_initialized", url=settings.REDIS_URL)
    return redis_client


async def close_redis_pool() -> None:
    """
    Closes the Redis async connection pool on app shutdown.
    """
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        logger.info("redis_pool_closed")
        redis_client = None
