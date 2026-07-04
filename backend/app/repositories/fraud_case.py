"""
FraudCase Repository Implementation.

Data access layer for FraudCase model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.enums import CaseStatus, CasePriority
from app.repositories.base import BaseRepository


class FraudCaseRepository(BaseRepository[FraudCase, Any, Any]):
    """
    Repository for FraudCase model.

    Provides fraud case-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(FraudCase, session)

    async def get_by_case_number(self, case_number: str) -> Optional[FraudCase]:
        """Get fraud case by case number."""
        return await self.get_by_field("case_number", case_number)

    async def get_by_alert_id(self, alert_id: str) -> Optional[FraudCase]:
        """Get fraud case by alert ID."""
        return await self.get_by_field("alert_id", alert_id)

    async def get_cases_by_status(
        self,
        status: CaseStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudCase]:
        """Get cases by status."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"status": status, "deleted_at": None}
        )

    async def get_cases_by_investigator(
        self,
        investigator_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudCase]:
        """Get cases assigned to an investigator."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"investigator_id": investigator_id, "deleted_at": None}
        )

    async def get_active_cases(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudCase]:
        """Get all open or in-progress cases."""
        result = await self.session.execute(
            select(FraudCase).where(
                FraudCase.status.in_([CaseStatus.NEW, CaseStatus.UNDER_INVESTIGATION, CaseStatus.ESCALATED]),
                FraudCase.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_confirmed_fraud_cases(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudCase]:
        """Get cases where fraud was confirmed."""
        result = await self.session.execute(
            select(FraudCase).where(
                FraudCase.fraud_confirmed == True,
                FraudCase.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: CaseStatus) -> int:
        """Count cases by status."""
        result = await self.session.execute(
            select(func.count()).select_from(FraudCase).where(
                FraudCase.status == status,
                FraudCase.deleted_at.is_(None)
            )
        )
        return result.scalar_one()
