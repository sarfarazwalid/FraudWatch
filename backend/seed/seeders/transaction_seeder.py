"""Transaction seeder - generates 10,000+ realistic transactions with fraud patterns."""
import random
from datetime import datetime, timedelta
from seed.base import BaseSeeder
from seed.utils import (
    fake, random_amount, random_timestamp, random_bangladesh_location,
    generate_transaction_ref, get_fraud_pattern
)
from app.models.transaction.transaction import Transaction
from app.models.enums import TransactionStatusValue

FRAUD_TYPES = [
    "velocity", "impossible_travel", "high_value", "new_device",
    "dormant", "round_amount", "card_testing", "merchant_abuse", "synthetic"
]

class TransactionSeeder(BaseSeeder):
    async def seed(self, count: int = 10000) -> dict[str, int]:
        records = []
        statuses = [
            TransactionStatusValue.COMPLETED, TransactionStatusValue.COMPLETED,
            TransactionStatusValue.COMPLETED, TransactionStatusValue.COMPLETED,
            TransactionStatusValue.PENDING, TransactionStatusValue.FLAGGED,
            TransactionStatusValue.FAILED
        ]
        for i in range(count):
            # ~3% get fraud patterns
            is_fraud = random.random() < 0.03
            fraud_type = random.choice(FRAUD_TYPES) if is_fraud else None
            amount = random_amount()
            ts = random_timestamp()
            status = TransactionStatusValue.FLAGGED if is_fraud else random.choice(statuses)
            records.append({
                "transaction_ref": generate_transaction_ref(i + 1),
                "amount": amount,
                "currency": "BDT",
                "status": status,
                "timestamp": ts,
                "is_flagged": is_fraud,
                "fraud_score": random.uniform(70, 100) if is_fraud else random.uniform(0, 30),
                "metadata": get_fraud_pattern({}, fraud_type) if fraud_type else None,
            })
        await self.bulk_insert_batched(Transaction, records)
        self.add_stat("transactions", len(records))
        return self.get_stats()
    async def clear(self):
        await self.clear_table("transactions")