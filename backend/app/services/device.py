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

    async def list_devices(
        self, page: int = 1, page_size: int = 20, search: Optional[str] = None,
        filters: Optional[dict] = None, sort_by: str = "created_at", sort_order: str = "desc",
    ) -> tuple[List[Device], int]:
        skip = (page - 1) * page_size
        repo_filters = {}
        if filters:
            for k in ("device_type", "is_trusted", "is_active"):
                if k in filters and filters[k] is not None:
                    repo_filters[k] = filters[k]
        if search:
            devices = await self.device_repo.search_devices(search, skip, page_size)
            total = len(devices)
        else:
            devices = await self.device_repo.get_all(
                skip=skip, limit=page_size, filters=repo_filters or None,
                order_by=sort_by if sort_order == "asc" else f"-{sort_by}",
            )
            total = await self.device_repo.count(filters=repo_filters or None)
        return devices, total

    async def deactivate_device(self, device_id: str) -> bool:
        device = await self.device_repo.get(device_id)
        if not device: return False
        device.is_active = False
        await self.device_repo.session.flush()
        return True
