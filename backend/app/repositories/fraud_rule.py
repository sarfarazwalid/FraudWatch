"""
FraudRule Repository Implementation.

Data access layer for FraudRule model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.fraud.fraud_rule import FraudRule
from app.repositories.base import BaseRepository


class FraudRuleRepository(BaseRepository[FraudRule, Any, Any]):
    """
    Repository for FraudRule model.

    Provides fraud rule-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(FraudRule, session)

    async def get_by_rule_code(self, rule_code: str) -> Optional[FraudRule]:
        """Get fraud rule by rule code."""
        return await self.get_by_field("rule_code", rule_code)

    async def get_active_rules(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudRule]:
        """Get all active rules."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True, "deleted_at": None}
        )

    async def get_rules_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudRule]:
        """Get rules by category."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"rule_category": category, "deleted_at": None}
        )

    async def get_rules_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudRule]:
        """Get rules by severity."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"severity": severity, "deleted_at": None}
        )
