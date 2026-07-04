"""
Seeder for reference data: currencies, payment methods, transaction types, statuses, risk levels.
"""

from seed.base import BaseSeeder
from seed.utils import CURRENCIES, PAYMENT_METHODS, TRANSACTION_TYPES, TRANSACTION_STATUSES, RISK_LEVELS
from app.models.transaction.currency import Currency
from app.models.transaction.payment_method import PaymentMethod
from app.models.transaction.transaction_type import TransactionType
from app.models.transaction.transaction_status import TransactionStatusModel
from app.models.transaction.risk_level import RiskLevelCode


class ReferenceDataSeeder(BaseSeeder):
    """Seed reference/lookup data."""

    async def seed(self) -> dict[str, int]:
        # Currencies
        await self.bulk_insert(Currency, [
            {"code": c["code"], "name": c["name"], "symbol": c["symbol"],
             "decimal_places": c["decimal_places"], "is_active": c["is_active"]}
            for c in CURRENCIES
        ])
        self.add_stat("currencies", len(CURRENCIES))

        # Payment Methods
        await self.bulk_insert(PaymentMethod, [
            {"code": p["code"], "name": p["name"], "category": p["category"]}
            for p in PAYMENT_METHODS
        ])
        self.add_stat("payment_methods", len(PAYMENT_METHODS))

        # Transaction Types
        await self.bulk_insert(TransactionType, [
            {"code": t["code"], "name": t["name"], "description": t["description"]}
            for t in TRANSACTION_TYPES
        ])
        self.add_stat("transaction_types", len(TRANSACTION_TYPES))

        # Transaction Statuses
        await self.bulk_insert(TransactionStatusModel, [
            {"code": s["code"], "name": s["name"], "description": s["description"]}
            for s in TRANSACTION_STATUSES
        ])
        self.add_stat("transaction_statuses", len(TRANSACTION_STATUSES))

        # Risk Levels
        await self.bulk_insert(RiskLevelCode, [
            {"code": r["code"], "name": r["name"], "description": r["description"],
             "score_min": r["score_min"], "score_max": r["score_max"]}
            for r in RISK_LEVELS
        ])
        self.add_stat("risk_levels", len(RISK_LEVELS))

        return self.get_stats()

    async def clear(self):
        await self.clear_table("currencies")
        await self.clear_table("payment_methods")
        await self.clear_table("transaction_types")
        await self.clear_table("transaction_statuses")
        await self.clear_table("risk_levels")