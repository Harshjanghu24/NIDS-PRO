"""
Phase D — Authentication & Security Tests.

Tests cover: registration, login (success/failure), token refresh,
protected route (GET /auth/me) access with/without token,
role-restricted route access, and audit logging of failed logins.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import (
    get_audit_repository,
    get_current_user,
    get_role_repository,
    get_user_repository,
    require_role,
)
from app.core.database import Base, get_db_session
from app.core.security import create_access_token, hash_password
from app.infrastructure.repositories.audit_repository import AuditRepository
from app.infrastructure.repositories.models import User
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.main import app


# ── Fixtures ──


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession):
    """
    HTTPX AsyncClient wired to a fresh in-memory SQLite DB.
    Overrides the DB session dependency so all repos share the same session/transaction.
    """

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_user(db_session: AsyncSession):
    """Pre-seed a user with a known password and ANALYST role for login tests."""
    role_repo = RoleRepository(db_session)
    user_repo = UserRepository(db_session)

    role = await role_repo.create(role_name="ANALYST", description="SOC Analyst")
    viewer = await role_repo.create(role_name="VIEWER", description="Read-only")
    user = await user_repo.create(
        username="testanalyst",
        email="analyst@test.com",
        password_hash=hash_password("Str0ngP@ss!"),
    )
    await user_repo.assign_role(user, role)
    await db_session.commit()
    return user


# ── Registration Tests ──


@pytest.mark.asyncio
async def test_register_success(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v2/auth/register",
        json={"username": "newuser", "email": "new@test.com", "password": "SecureP@ss1"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@test.com"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["role_name"] == "VIEWER"


@pytest.mark.asyncio
async def test_register_duplicate_username(auth_client: AsyncClient):
    await auth_client.post(
        "/api/v2/auth/register",
        json={"username": "dupuser", "email": "dup1@test.com", "password": "SecureP@ss1"},
    )
    resp = await auth_client.post(
        "/api/v2/auth/register",
        json={"username": "dupuser", "email": "dup2@test.com", "password": "SecureP@ss1"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_client: AsyncClient):
    await auth_client.post(
        "/api/v2/auth/register",
        json={"username": "emailuser1", "email": "same@test.com", "password": "SecureP@ss1"},
    )
    resp = await auth_client.post(
        "/api/v2/auth/register",
        json={"username": "emailuser2", "email": "same@test.com", "password": "SecureP@ss1"},
    )
    assert resp.status_code == 409


# ── Login Tests ──


@pytest.mark.asyncio
async def test_login_success(auth_client: AsyncClient, seeded_user: User):
    resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Check refresh cookie is set
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(auth_client: AsyncClient, seeded_user: User):
    resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "WrongPassword123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "doesnotexist", "password": "anypass123"},
    )
    assert resp.status_code == 401


# ── Protected Route Tests (GET /auth/me) ──


@pytest.mark.asyncio
async def test_me_without_token(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v2/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(auth_client: AsyncClient, seeded_user: User):
    # Login first
    login_resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    token = login_resp.json()["access_token"]

    resp = await auth_client.get(
        "/api/v2/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testanalyst"
    assert any(r["role_name"] == "ANALYST" for r in data["roles"])


@pytest.mark.asyncio
async def test_me_with_invalid_token(auth_client: AsyncClient):
    resp = await auth_client.get(
        "/api/v2/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code == 401


# ── Token Refresh Tests ──


@pytest.mark.asyncio
async def test_refresh_success(auth_client: AsyncClient, seeded_user: User):
    # Login to get refresh cookie
    login_resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    assert login_resp.status_code == 200

    # The cookies should be carried forward by httpx
    refresh_resp = await auth_client.post("/api/v2/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


@pytest.mark.asyncio
async def test_refresh_without_cookie(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v2/auth/refresh")
    assert resp.status_code == 401


# ── Logout Test ──


@pytest.mark.asyncio
async def test_logout(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v2/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


# ── Role-Restricted Route Tests ──


@pytest.mark.asyncio
async def test_role_restricted_access_granted(auth_client: AsyncClient, seeded_user: User):
    """ANALYST-required route should accept a user with ANALYST role."""
    # Add a test-only route requiring ANALYST role
    from fastapi import APIRouter, Depends

    test_router = APIRouter()

    @test_router.get("/api/v2/test-admin-only")
    async def _admin_route(user: User = Depends(require_role("ANALYST"))):
        return {"ok": True}

    app.include_router(test_router)

    # Login as analyst
    login_resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    token = login_resp.json()["access_token"]

    resp = await auth_client.get(
        "/api/v2/test-admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_role_restricted_access_denied(auth_client: AsyncClient, seeded_user: User):
    """ADMIN-required route should reject a user who only has ANALYST role."""
    from fastapi import APIRouter, Depends

    test_router = APIRouter()

    @test_router.get("/api/v2/test-admin-denied")
    async def _admin_only(user: User = Depends(require_role("ADMIN"))):
        return {"ok": True}

    app.include_router(test_router)

    # Login as analyst (does not have ADMIN)
    login_resp = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    token = login_resp.json()["access_token"]

    resp = await auth_client.get(
        "/api/v2/test-admin-denied",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── Audit Logging Tests ──


@pytest.mark.asyncio
async def test_failed_login_audit_logged(auth_client: AsyncClient, db_session: AsyncSession, seeded_user: User):
    """Failed login attempt should create an audit log entry."""
    await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "WrongPassword123"},
    )

    audit_repo = AuditRepository(db_session)
    logs = await audit_repo.get_by_user(seeded_user.id)
    failed_logins = [l for l in logs if l.action_type == "LOGIN_FAILED"]
    assert len(failed_logins) >= 1


# ── Refresh with invalid sub claim ──


@pytest.mark.asyncio
async def test_refresh_invalid_sub_returns_401(auth_client: AsyncClient):
    """A refresh token whose 'sub' is not a valid UUID must return 401, not 500."""
    from app.core.security import create_refresh_token

    # Craft a token with a non-UUID sub claim
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    bad_payload = {
        "sub": "not-a-uuid",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "type": "refresh",
    }
    bad_token = pyjwt.encode(bad_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Set the cookie manually and call /refresh
    auth_client.cookies.set("refresh_token", bad_token, domain="testserver", path="/api/v2/auth")
    resp = await auth_client.post("/api/v2/auth/refresh")
    assert resp.status_code == 401, f"Expected 401 but got {resp.status_code}"


# ── Cookie secure flag reflects ENVIRONMENT ──


@pytest.mark.asyncio
async def test_cookie_secure_flag_reflects_environment(auth_client: AsyncClient, seeded_user: User):
    """The refresh cookie 'secure' attribute should be True only in production."""
    from unittest.mock import patch
    from app.core.config import settings

    # In development (default), cookie should NOT be secure
    resp_dev = await auth_client.post(
        "/api/v2/auth/login",
        json={"username": "testanalyst", "password": "Str0ngP@ss!"},
    )
    assert resp_dev.status_code == 200
    set_cookie_dev = resp_dev.headers.get("set-cookie", "")
    # "Secure" should NOT appear when ENVIRONMENT != "production"
    assert "secure" not in set_cookie_dev.lower().split("httponly")[0].split("samesite")[0] or settings.ENVIRONMENT == "production"

    # Patch ENVIRONMENT to "production" and verify secure flag appears
    with patch.object(settings, "ENVIRONMENT", "production"):
        resp_prod = await auth_client.post(
            "/api/v2/auth/login",
            json={"username": "testanalyst", "password": "Str0ngP@ss!"},
        )
        assert resp_prod.status_code == 200
        set_cookie_prod = resp_prod.headers.get("set-cookie", "")
        assert "secure" in set_cookie_prod.lower()
