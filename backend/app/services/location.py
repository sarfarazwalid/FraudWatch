"""
Location service.

Handles location management business logic.
"""

from typing import Optional, List, Dict, Any

from app.models.transaction.location import Location
from app.repositories.location import LocationRepository


class LocationService:
    """
    Service for location operations.

    Handles location creation, updates, and retrieval.
    """

    def __init__(self, location_repo: LocationRepository):
        self.location_repo = location_repo

    async def create_location(self, location_data: Dict[str, Any]) -> Location:
        """
        Create a new location.

        Args:
            location_data: Location creation data

        Returns:
            Created location
        """
        location = Location(**location_data)
        self.location_repo.session.add(location)
        await self.location_repo.session.flush()
        await self.location_repo.session.refresh(location)
        return location

    async def get_location(self, location_id: str) -> Optional[Location]:
        """Get location by ID."""
        return await self.location_repo.get(location_id)

    async def update_location(self, location_id: str, update_data: Dict[str, Any]) -> Optional[Location]:
        """Update location."""
        location = await self.location_repo.get(location_id)
        if not location:
            return None

        for field, value in update_data.items():
            if hasattr(location, field) and value is not None:
                setattr(location, field, value)

        await self.location_repo.session.flush()
        await self.location_repo.session.refresh(location)
        return location

    async def get_active_locations(self, skip: int = 0, limit: int = 100) -> List[Location]:
        """Get all active locations."""
        return await self.location_repo.get_active_locations(skip, limit)
