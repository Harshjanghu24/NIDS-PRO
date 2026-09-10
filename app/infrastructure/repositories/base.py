from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Async Repository providing standard CRUD database access logic.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id_val)
        )
        return result.scalar_one_or_none()

    async def list(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """Fetch a paginated list of records matching optional field filters."""
        query = select(self.model)
        for attr, val in filters.items():
            if hasattr(self.model, attr) and val is not None:
                query = query.where(getattr(self.model, attr) == val)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **attributes) -> ModelType:
        """Create and persist a new record instance."""
        instance = self.model(**attributes)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **attributes) -> ModelType:
        """Update fields on an existing entity instance."""
        for attr, val in attributes.items():
            if hasattr(instance, attr):
                setattr(instance, attr, val)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> bool:
        """Delete an existing entity instance."""
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def count(self, **filters) -> int:
        """Count total matching records."""
        query = select(func.count()).select_from(self.model)
        for attr, val in filters.items():
            if hasattr(self.model, attr) and val is not None:
                query = query.where(getattr(self.model, attr) == val)
        result = await self.session.execute(query)
        return result.scalar() or 0
