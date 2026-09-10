import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.infrastructure.repositories.audit_repository import AuditRepository
from app.infrastructure.repositories.model_repository import ModelRepository
from app.infrastructure.repositories.prediction_repository import PredictionRepository
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def test_db_session() -> AsyncSession:
    """Provides an isolated in-memory SQLite database session for repository testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_role_repository_crud(test_db_session: AsyncSession):
    repo = RoleRepository(test_db_session)
    admin_role = await repo.create(
        role_name="ADMIN", description="Administrator Role"
    )
    assert admin_role.id is not None
    assert admin_role.role_name == "ADMIN"

    fetched = await repo.get_by_name("admin")
    assert fetched is not None
    assert fetched.id == admin_role.id


@pytest.mark.asyncio
async def test_user_repository_crud(test_db_session: AsyncSession):
    user_repo = UserRepository(test_db_session)
    role_repo = RoleRepository(test_db_session)

    # Create role and user
    analyst_role = await role_repo.create(
        role_name="ANALYST", description="SOC Analyst"
    )
    user = await user_repo.create(
        username="sec_analyst",
        email="analyst@enterprise.sec",
        password_hash="salted_bcrypt_hash_placeholder",
    )
    assert user.id is not None

    # Test lookup
    found_by_user = await user_repo.get_by_username("sec_analyst")
    assert found_by_user is not None
    assert found_by_user.email == "analyst@enterprise.sec"

    found_by_email = await user_repo.get_by_email("analyst@enterprise.sec")
    assert found_by_email is not None

    # Assign role
    updated_user = await user_repo.assign_role(user, analyst_role)
    assert len(updated_user.roles) == 1
    assert updated_user.roles[0].role_name == "ANALYST"


@pytest.mark.asyncio
async def test_model_repository_crud(test_db_session: AsyncSession):
    repo = ModelRepository(test_db_session)
    model1 = await repo.create(
        model_name="XGBoost Baseline",
        version="v2.1.0",
        model_type="XGBOOST",
        artifact_path="/artifacts/models/xgb_v1.pkl",
        validation_metrics={"macro_f1": 0.88, "accuracy": 0.94},
    )
    assert model1.id is not None
    assert model1.is_active is False

    # Hot-swap model to active
    activated = await repo.set_active_model(model1.id)
    assert activated is not None
    assert activated.is_active is True

    current_active = await repo.get_active_model()
    assert current_active is not None
    assert current_active.id == model1.id


@pytest.mark.asyncio
async def test_prediction_repository_crud(test_db_session: AsyncSession):
    repo = PredictionRepository(test_db_session)

    # 1. Create flow record
    flow = await repo.create_flow(
        raw_41_features={"duration": 0.0, "src_bytes": 215, "dst_bytes": 4500},
        predicted_category="U2R",
        confidence_score=0.962,
        inference_latency_ms=8.45,
        source_ip="192.168.1.105",
        destination_port=22,
        protocol_type="tcp",
    )
    assert flow.id is not None
    assert flow.predicted_category == "U2R"

    # 2. Create alert
    alert = await repo.create_alert(
        flow_id=flow.id,
        attack_category="U2R",
        severity_level="CRITICAL",
        shap_attributions={"num_root": 0.42, "root_shell": 0.28},
    )
    assert alert.id is not None
    assert alert.status == "NEW"

    # 3. List alerts filter
    alerts_list = await repo.list_alerts(severity="CRITICAL", status_val="NEW")
    assert len(alerts_list) == 1
    assert alerts_list[0].id == alert.id

    # 4. Triage alert
    triaged = await repo.add_triage_entry(
        alert=alert,
        analyst_user_id=uuid.uuid4(),
        new_status="ACKNOWLEDGED",
        notes="Investigating suspicious SSH escalation.",
    )
    assert triaged.new_status == "ACKNOWLEDGED"
    assert alert.status == "ACKNOWLEDGED"


@pytest.mark.asyncio
async def test_audit_repository_crud(test_db_session: AsyncSession):
    repo = AuditRepository(test_db_session)
    user_id = uuid.uuid4()

    log_entry = await repo.log_action(
        action_type="MODEL_HOTSWAP",
        user_id=user_id,
        resource_target="model_v2.1.0",
        action_details={"previous": "v2.0.0", "new": "v2.1.0"},
        ip_address="10.0.0.4",
    )
    assert log_entry.id is not None

    user_logs = await repo.get_by_user(user_id)
    assert len(user_logs) == 1
    assert user_logs[0].action_type == "MODEL_HOTSWAP"
