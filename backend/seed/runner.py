"""Seed runner - orchestrates all seeders."""
import asyncio
import time
from argparse import ArgumentParser
from typing import Optional
from seed.base import BaseSeeder
from seed.seeders.reference_seeder import ReferenceDataSeeder
from seed.seeders.identity_seeder import IdentitySeeder
from seed.seeders.merchant_seeder import MerchantSeeder
from seed.seeders.agent_seeder import AgentSeeder
from seed.seeders.device_seeder import DeviceSeeder
from seed.seeders.location_seeder import LocationSeeder
from seed.seeders.transaction_seeder import TransactionSeeder
from seed.seeders.fraud_rule_seeder import FraudRuleSeeder
from seed.seeders.model_registry_seeder import ModelRegistrySeeder
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import AsyncSessionLocal

SEEDERS = [
    ("reference", ReferenceDataSeeder),
    ("identity", IdentitySeeder),
    ("merchants", MerchantSeeder),
    ("agents", AgentSeeder),
    ("devices", DeviceSeeder),
    ("locations", LocationSeeder),
    ("transactions", TransactionSeeder),
    ("fraud_rules", FraudRuleSeeder),
    ("model_registry", ModelRegistrySeeder),
]

class SeedRunner:
    async def run(self, seeder_names: list[str], reset: bool = False, transaction_count: Optional[int] = None):
        start = time.time()
        total_stats = {}
        async with AsyncSessionLocal() as session:
            for name, seeder_cls in SEEDERS:
                if seeder_names and name not in seeder_names:
                    continue
                seeder: BaseSeeder = seeder_cls(session)
                print(f"Seeding {name}...")
                if reset:
                    await seeder.clear()
                if name == "transactions" and transaction_count:
                    stats = await seeder.seed(transaction_count)
                else:
                    stats = await seeder.seed()
                total_stats.update(stats)
                for k, v in stats.items():
                    print(f"  {k}: {v}")
                await session.commit()
        elapsed = time.time() - start
        print(f"\nCompleted in {elapsed:.2f}s")
        print("Summary:", total_stats)

    async def reset_all(self):
        async with AsyncSessionLocal() as session:
            for _, seeder_cls in reversed(SEEDERS):
                seeder = seeder_cls(session)
                try:
                    await seeder.clear()
                except Exception:
                    pass
            await session.commit()
        print("Database reset complete")

def main():
    parser = ArgumentParser(description="FraudWatch Database Seeder")
    parser.add_argument("--reset", action="store_true", help="Clear tables before seeding")
    parser.add_argument("--seeders", nargs="+", help="Run specific seeders")
    parser.add_argument("--transactions", type=int, default=10000, help="Number of transactions")
    parser.add_argument("--reset-only", action="store_true", help="Only reset database")
    args = parser.parse_args()
    runner = SeedRunner()
    if args.reset_only:
        asyncio.run(runner.reset_all())
        return
    seeder_names = args.seeders or []
    asyncio.run(runner.run(seeder_names, reset=args.reset, transaction_count=args.transactions))

if __name__ == "__main__":
    main()