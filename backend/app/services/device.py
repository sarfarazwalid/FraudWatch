"""
Device service.

Handles device management business logic.
"""

from typing import Optional, List

from app.models.transaction.device import Device
from app.repositories.device import DeviceRepository


class DeviceService:
    """
    Service for device operations.

    Handles device creation, updates, and retrieval.
    """

    def __init__(self, device_repo: DeviceRepository):
        self.device_repo = device_repo

    async def create_device(self, device_data: dict) -> Device:
        """
        Create a new device.

        Args:
            device_data: Device creation data

        Returns:
            Created device
        """
        device = Device(**device_data)
        self.device_repo.session.add(device)
        await self.device_repo.session.flush()
        await self.device_repo.session.refresh(device)
        return device

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID."""
        return await self.device_repo.get(device_id)

    async def get_device_by_fingerprint(self, fingerprint: str) -> Optional[Device]:
        """Get device by fingerprint."""
        return await self.device_repo.get_by_device_fingerprint(fingerprint)

    async def update_device(self, device_id: str, update_data: dict) -> Optional[Device]:
        """Update device."""
        device = await self.device_repo.get(device_id)
        if not device:
            return None

        for field, value in update_data.items():
            if hasattr(device, field) and value is not None:
                setattr(device, field, value)

        await self.device_repo.session.flush()
        await self.device_repo.session.refresh(device)
        return device

    async def get_active_devices(self, skip: int = 0, limit: int = 100) -> List[Device]:
        """Get all active devices."""
        return await self.device_repo.get_active_devices(skip, limit)
