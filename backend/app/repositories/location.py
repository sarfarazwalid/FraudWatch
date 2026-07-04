"""
Location Repository Implementation.

Data access layer for Location model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.transaction.location import Location
from app.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location, Any, Any]):
    """
    Repository for Location model.

    Provides location-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Location, session)

    async def get_by_location_code(self, location_code: str) -> Optional[Location]:
        """Get location by location code."""
        return await self.get_by_field("location_code", location_code)

    async def get_active_locations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Location]:
        """Get all active locations."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True, "deleted_at": None}
        )
