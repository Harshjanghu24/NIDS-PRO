from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.repositories.models import AuditLog


class AuditRepository(BaseRepository[AuditLog]):
    """
    Repository managing audit trails of security operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log_action(
        self,
        action_type: str,
        user_id: Optional[uuid.UUID] = None,
        resource_target: Optional[str] = None,
        action_details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create audit log entry."""
        audit_entry = AuditLog(
            action_type=action_type,
            user_id=user_id,
            resource_target=resource_target,
            action_details=action_details,
            ip_address=ip_address,
        )
        self.session.add(audit_entry)
        await self.session.flush()
        await self.session.refresh(audit_entry)
        return audit_entry

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[AuditLog]:
        """Fetch audit log entries by user ID."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.performed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
