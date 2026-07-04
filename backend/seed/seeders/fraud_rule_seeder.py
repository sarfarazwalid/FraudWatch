"""Fraud rule seeder - generates fraud detection rules."""
from seed.base import BaseSeeder
from seed.utils import FRAUD_RULES
from app.models.fraud.fraud_rule import FraudRule

class FraudRuleSeeder(BaseSeeder):
    async def seed(self) -> dict[str, int]:
        records = []
        for rule in FRAUD_RULES:
            records.append({
                "name": rule["name"],
                "description": rule["description"],
                "category": rule["category"],
                "severity": rule["severity"],
                "is_active": True,
            })
        await self.bulk_insert(FraudRule, records)
        self.add_stat("fraud_rules", len(records))
        return self.get_stats()
    async def clear(self):
        await self.clear_table("fraud_rules")