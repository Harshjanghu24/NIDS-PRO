from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.repositories.models import Role


class RoleRepository(BaseRepository[Role]):
    """
    Repository for managing Role persistence.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_name(self, role_name: str) -> Optional[Role]:
        """Find role by unique role name (e.g. ADMIN, ANALYST, VIEWER)."""
        result = await self.session.execute(
            select(Role).where(Role.role_name == role_name.upper())
        )
        return result.scalar_one_or_none()
