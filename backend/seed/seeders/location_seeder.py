"""Location seeder - generates Bangladesh locations."""
from seed.base import BaseSeeder
from seed.utils import random_bangladesh_location
from app.models.transaction.location import Location

class LocationSeeder(BaseSeeder):
    async def seed(self) -> dict[str, int]:
        records = []
        for _ in range(60):
            loc = random_bangladesh_location()
            records.append({
                "division": loc["division"],
                "district": loc["district"],
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "country": loc["country"],
                "timezone": loc["timezone"],
                "is_active": True,
            })
        await self.bulk_insert(Location, records)
        self.add_stat("locations", len(records))
        return self.get_stats()
    async def clear(self):
        await self.clear_table("locations")