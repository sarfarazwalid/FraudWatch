"""
FraudRule service.

Handles fraud rule management business logic.
"""

from typing import Optional, List

from app.models.fraud.fraud_rule import FraudRule
from app.repositories.fraud_rule import FraudRuleRepository


class FraudRuleService:
    """
    Service for fraud rule operations.

    Handles rule creation, updates, and retrieval.
    """

    def __init__(self, fraud_rule_repo: FraudRuleRepository):
        self.fraud_rule_repo = fraud_rule_repo

    async def create_rule(self, rule_data: dict) -> FraudRule:
        """
        Create a new fraud rule.

        Args:
            rule_data: Rule creation data

        Returns:
            Created rule
        """
        rule = FraudRule(**rule_data)
        self.fraud_rule_repo.session.add(rule)
        await self.fraud_rule_repo.session.flush()
        await self.fraud_rule_repo.session.refresh(rule)
        return rule

    async def get_rule(self, rule_id: str) -> Optional[FraudRule]:
        """Get fraud rule by ID."""
        return await self.fraud_rule_repo.get(rule_id)

    async def get_rule_by_code(self, rule_code: str) -> Optional[FraudRule]:
        """Get fraud rule by rule code."""
        return await self.fraud_rule_repo.get_by_rule_code(rule_code)

    async def update_rule(self, rule_id: str, update_data: dict) -> Optional[FraudRule]:
        """Update fraud rule."""
        rule = await self.fraud_rule_repo.get(rule_id)
        if not rule:
            return None

        for field, value in update_data.items():
            if hasattr(rule, field) and value is not None:
                setattr(rule, field, value)

        await self.fraud_rule_repo.session.flush()
        await self.fraud_rule_repo.session.refresh(rule)
        return rule

    async def get_active_rules(self, skip: int = 0, limit: int = 100) -> List[FraudRule]:
        """Get all active rules."""
        return await self.fraud_rule_repo.get_active_rules(skip, limit)

    async def get_rules_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[FraudRule]:
        """Get rules by category."""
        return await self.fraud_rule_repo.get_rules_by_category(category, skip, limit)
