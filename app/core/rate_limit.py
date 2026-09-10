import time
from collections import defaultdict

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import redis_client
from app.core.logging import logger

# Rate limit config: 10 login attempts per 60-second window
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 60


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate-limits POST /api/v2/auth/login.
    Uses Redis if available, falls back to in-memory dict.
    """

    def __init__(self, app):
        super().__init__(app)
        self._local_store: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or request.url.path != "/api/v2/auth/login":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if await self._is_rate_limited(client_ip):
            logger.warning("login_rate_limited", ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many login attempts. Try again later."},
            )

        return await call_next(request)

    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check and increment the attempt counter. Returns True if limit exceeded."""
        if redis_client is not None:
            return await self._check_redis(client_ip)
        return self._check_local(client_ip)

    async def _check_redis(self, client_ip: str) -> bool:
        if redis_client is None:
            return self._check_local(client_ip)
        key = f"rate:login:{client_ip}"
        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, _WINDOW_SECONDS)
            return current > _MAX_ATTEMPTS
        except Exception:
            # If Redis fails, fall back to local store
            return self._check_local(client_ip)

    def _check_local(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - _WINDOW_SECONDS
        # Prune expired entries
        self._local_store[client_ip] = [
            ts for ts in self._local_store[client_ip] if ts > window_start
        ]
        if len(self._local_store[client_ip]) >= _MAX_ATTEMPTS:
            return True
        self._local_store[client_ip].append(now)
        return False
