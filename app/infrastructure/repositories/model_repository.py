from typing import Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.repositories.models import ModelArtifact


class ModelRepository(BaseRepository[ModelArtifact]):
    """
    Repository managing MLOps Model Registry artifacts.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(ModelArtifact, session)

    async def get_active_model(self) -> Optional[ModelArtifact]:
        """Fetch the currently active classification model artifact."""
        result = await self.session.execute(
            select(ModelArtifact).where(ModelArtifact.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_by_version(self, version: str) -> Optional[ModelArtifact]:
        """Fetch model by unique version string."""
        result = await self.session.execute(
            select(ModelArtifact).where(ModelArtifact.version == version)
        )
        return result.scalar_one_or_none()

    async def set_active_model(self, model_id: uuid.UUID) -> Optional[ModelArtifact]:
        """Hot-swap the active model (deactivates all others, activates targeted model)."""
        # Deactivate all existing models
        await self.session.execute(
            update(ModelArtifact).values(is_active=False)
        )
        # Activate targeted model
        target = await self.get_by_id(model_id)
        if target:
            target.is_active = True
            await self.session.flush()
            await self.session.refresh(target)
        return target
