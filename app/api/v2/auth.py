import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.dependencies import (
    get_audit_repository,
    get_current_user,
    get_role_repository,
    get_user_repository,
)
from app.api.v2.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.infrastructure.repositories.audit_repository import AuditRepository
from app.infrastructure.repositories.models import User
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Cookie settings for refresh token
_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/api/v2/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/v2/auth")


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
):
    # Check uniqueness
    if await user_repo.get_by_username(body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    if await user_repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user with hashed password
    user = await user_repo.create(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )

    # Assign default VIEWER role (create if missing)
    default_role = await role_repo.get_by_name("VIEWER")
    if not default_role:
        default_role = await role_repo.create(
            role_name="VIEWER", description="Default read-only role"
        )
    await user_repo.assign_role(user, default_role)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain tokens",
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    user = await user_repo.get_by_username(body.username)
    ip = _client_ip(request)

    if not user or not verify_password(body.password, user.password_hash):
        # Audit failed login attempt
        await audit_repo.log_action(
            action_type="LOGIN_FAILED",
            resource_target=body.username,
            action_details={"reason": "invalid_credentials"},
            ip_address=ip,
            user_id=user.id if user else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Build token claims
    roles = [r.role_name for r in user.roles]
    access_token = create_access_token(
        subject=str(user.id), extra_claims={"roles": roles}
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    _set_refresh_cookie(response, refresh_token)

    # Audit successful login
    await audit_repo.log_action(
        action_type="LOGIN_SUCCESS",
        user_id=user.id,
        resource_target=user.username,
        ip_address=ip,
    )

    return TokenResponse(access_token=access_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token via refresh cookie",
)
async def refresh(
    request: Request,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
):
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = _uuid.UUID(payload["sub"])
    except Exception:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="User not found or inactive")

    roles = [r.role_name for r in user.roles]
    new_access = create_access_token(
        subject=str(user.id), extra_claims={"roles": roles}
    )

    # Rotate refresh token
    new_refresh = create_refresh_token(subject=str(user.id))
    _set_refresh_cookie(response, new_refresh)

    return TokenResponse(access_token=new_access)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout by clearing refresh cookie",
)
async def logout(response: Response):
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user profile",
)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
