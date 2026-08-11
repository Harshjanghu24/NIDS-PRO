from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.repositories.models import Role, User


class UserRepository(BaseRepository[User]):
    """
    Repository for managing User persistence and role associations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Find user by unique username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by unique email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def assign_role(self, user: User, role: Role) -> User:
        """Assign a role to a user if not already assigned."""
        if role not in user.roles:
            user.roles.append(role)
            await self.session.flush()
            await self.session.refresh(user)
        return user
