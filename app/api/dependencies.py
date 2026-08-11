import uuid as _uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import decode_token
from app.infrastructure.repositories.audit_repository import AuditRepository
from app.infrastructure.repositories.model_repository import ModelRepository
from app.infrastructure.repositories.models import User
from app.infrastructure.repositories.prediction_repository import PredictionRepository
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login", auto_error=True)


# ── Repository Dependencies ──


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


async def get_role_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RoleRepository:
    return RoleRepository(session)


async def get_prediction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PredictionRepository:
    return PredictionRepository(session)


async def get_audit_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AuditRepository:
    return AuditRepository(session)


async def get_model_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ModelRepository:
    return ModelRepository(session)


# ── Auth Dependencies ──


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """Validate JWT access token and return the authenticated User."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except Exception:
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    try:
        user_id = _uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_exc
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_role(role_name: str) -> Callable:
    """Factory returning a dependency that enforces a specific role."""

    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {r.role_name for r in current_user.roles}
        if role_name.upper() not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name.upper()}' required",
            )
        return current_user

    return _check_role
