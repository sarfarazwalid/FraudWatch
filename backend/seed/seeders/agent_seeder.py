"""
Seeder for agent data. Generates 100+ wallet agents.
"""

from seed.base import BaseSeeder
from seed.utils import fake, random_bangladesh_location, generate_agent_code
from app.models.transaction.agent import Agent


AGENT_ZONES = [
    "Dhaka Central", "Chattogram Port", "Khulna City", "Rajshahi Metro",
    "Sylhet Central", "Barishal City", "Rangpur Zone", "Mymensingh Zone",
    "Comilla Zone", "Cox's Bazar", "Jessore Zone", "Bogra Zone",
    "Tangail Zone", "Faridpur Zone", "Dinajpur Zone", "Kurigram Zone",
]


class AgentSeeder(BaseSeeder):
    """Seed wallet agent data."""

    async def seed(self) -> dict[str, int]:
        records = []
        for i in range(120):
            loc = random_bangladesh_location()
            zone = AGENT_ZONES[i % len(AGENT_ZONES)]
            statuses = ["active", "active", "active", "active", "inactive"]
            records.append({
                "agent_code": generate_agent_code(i + 1),
                "zone": zone,
                "location": f"{loc['district']}, {loc['division']}",
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "contact_number": fake.phone_number(),
                "status": fake.random_element(statuses),
                "is_active": True,
            })

        await self.bulk_insert(Agent, records)
        self.add_stat("agents", len(records))
        return self.get_stats()

    async def clear(self):
        await self.clear_table("agents")