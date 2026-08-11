"""Initial Database Schema V2.0

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-04 00:57:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create USERS table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # 2. Create ROLES table
    roles_table = op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_roles_role_name", "roles", ["role_name"], unique=True)

    # Pre-populate Default Roles
    op.bulk_insert(
        roles_table,
        [
            {"id": 1, "role_name": "ADMIN", "description": "Full System & Security Administrator"},
            {"id": 2, "role_name": "ANALYST", "description": "Security Operations Center Analyst"},
            {"id": 3, "role_name": "VIEWER", "description": "Read-Only Dashboard Viewer"},
        ],
    )

    # 3. Create USER_ROLES junction table
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. Create MODELS table
    op.create_table(
        "models",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("validation_metrics", sa.JSON(), nullable=True),
        sa.Column("registered_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_models_version", "models", ["version"], unique=True)

    # 5. Create FLOW_HISTORY table
    op.create_table(
        "flow_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("destination_ip", sa.String(length=45), nullable=True),
        sa.Column("destination_port", sa.Integer(), nullable=True),
        sa.Column("protocol_type", sa.String(length=10), nullable=True),
        sa.Column("raw_41_features", sa.JSON(), nullable=False),
        sa.Column("predicted_category", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("inference_latency_ms", sa.Float(), nullable=False),
        sa.Column("model_id", sa.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("idx_flow_history_time_cat", "flow_history", ["captured_at", "predicted_category"])

    # 6. Create ALERTS table
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("flow_id", sa.BigInteger(), sa.ForeignKey("flow_history.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("alert_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("attack_category", sa.String(length=20), nullable=False),
        sa.Column("severity_level", sa.String(length=15), nullable=False),
        sa.Column("shap_attributions", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_alerts_status_severity", "alerts", ["status", "severity_level"])

    # 7. Create ALERT_TRIAGE table
    op.create_table(
        "alert_triage",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", sa.UUID(as_uuid=True), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analyst_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("previous_status", sa.String(length=20), nullable=False),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("triaged_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 8. Create AUDIT_LOGS table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("resource_target", sa.String(length=255), nullable=True),
        sa.Column("action_details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_user_time", "audit_logs", ["user_id", "performed_at"])

    # 9. Create SYSTEM_SETTINGS table
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("data_type", sa.String(length=20), nullable=False, server_default="STRING"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_index("idx_audit_user_time", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("alert_triage")
    op.drop_index("idx_alerts_status_severity", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("idx_flow_history_time_cat", table_name="flow_history")
    op.drop_table("flow_history")
    op.drop_index("ix_models_version", table_name="models")
    op.drop_table("models")
    op.drop_table("user_roles")
    op.drop_index("ix_roles_role_name", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
