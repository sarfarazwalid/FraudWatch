"""Device seeder - generates 200 realistic devices."""
from seed.base import BaseSeeder
from seed.utils import fake, random_device
from app.models.transaction.device import Device

class DeviceSeeder(BaseSeeder):
    async def seed(self) -> dict[str, int]:
        records = []
        for _ in range(200):
            dev = random_device()
            records.append({
                "device_fingerprint": dev["device_fingerprint"],
                "device_type": dev["device_type"],
                "os": dev["os"],
                "browser": dev["browser"],
                "device_model": dev["device_model"],
                "is_mobile": dev["is_mobile"],
                "is_active": True,
            })
        await self.bulk_insert(Device, records)
        self.add_stat("devices", len(records))
        return self.get_stats()
    async def clear(self):
        await self.clear_table("devices")