import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.core.database import Base


# Cross-dialect JSON column helper to support both PostgreSQL JSONB and SQLite JSON in tests
class DialectJSON(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


# UserRole Association Table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_roles, back_populates="users", lazy="selectin"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    models_registered: Mapped[List["ModelArtifact"]] = relationship(
        "ModelArtifact", back_populates="registered_by_user"
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_roles, back_populates="roles"
    )


class ModelArtifact(Base):
    __tablename__ = "models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # XGBOOST, SGD_OOC, RANDOM_FOREST
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    validation_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        DialectJSON, nullable=True
    )
    registered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    registered_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="models_registered"
    )
    flows: Mapped[List["FlowHistory"]] = relationship(
        "FlowHistory", back_populates="model"
    )


class FlowHistory(Base):
    __tablename__ = "flow_history"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    destination_port: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    protocol_type: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    raw_41_features: Mapped[Dict[str, Any]] = mapped_column(
        DialectJSON, nullable=False
    )
    predicted_category: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # Normal, DOS, PROBE, R2L, U2R
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    inference_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("models.id", ondelete="SET NULL"), nullable=True
    )

    model: Mapped[Optional["ModelArtifact"]] = relationship(
        "ModelArtifact", back_populates="flows"
    )
    alert: Mapped[Optional["Alert"]] = relationship(
        "Alert", back_populates="flow", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_flow_history_time_cat",
            "captured_at",
            "predicted_category",
        ),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    flow_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("flow_history.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    alert_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    attack_category: Mapped[str] = mapped_column(String(20), nullable=False)
    severity_level: Mapped[str] = mapped_column(
        String(15), nullable=False
    )  # CRITICAL, HIGH, MEDIUM, LOW
    shap_attributions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        DialectJSON, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="NEW", nullable=False
    )  # NEW, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    flow: Mapped["FlowHistory"] = relationship("FlowHistory", back_populates="alert")
    triage_history: Mapped[List["AlertTriage"]] = relationship(
        "AlertTriage", back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_alerts_status_severity", "status", "severity_level"),
    )


class AlertTriage(Base):
    __tablename__ = "alert_triage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    analyst_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triaged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    alert: Mapped["Alert"] = relationship("Alert", back_populates="triage_history")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # LOGIN, MODEL_SWAP, CONFIG_CHANGE, ALERT_UPDATE
    resource_target: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    action_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        DialectJSON, nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="audit_logs"
    )

    __table_args__ = (Index("idx_audit_user_time", "user_id", "performed_at"),)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(
        String(20), default="STRING", nullable=False
    )  # STRING, INT, FLOAT, BOOL, JSON
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
