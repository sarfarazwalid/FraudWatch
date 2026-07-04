"""
Device Repository Implementation.

Data access layer for Device model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.transaction.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device, Any, Any]):
    """
    Repository for Device model.

    Provides device-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Device, session)

    async def get_by_device_fingerprint(self, device_fingerprint: str) -> Optional[Device]:
        """Get device by fingerprint."""
        return await self.get_by_field("device_fingerprint", device_fingerprint)

    async def get_active_devices(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Device]:
        """Get all active devices."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True, "deleted_at": None}
        )

    async def get_high_risk_devices(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Device]:
        """Get high-risk devices."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"risk_level": "high", "deleted_at": None}
        )
