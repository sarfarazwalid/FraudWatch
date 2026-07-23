"""
FraudCase service.

Handles fraud investigation case business logic and workflow management.
"""

from typing import Optional, List
from datetime import datetime

from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.enums import CaseStatus, CasePriority
from app.repositories.fraud_case import FraudCaseRepository


class FraudCaseService:
    """
    Service for fraud case operations.

    Handles case creation, investigator assignment, and status transitions.
    """

    def __init__(self, fraud_case_repo: FraudCaseRepository):
        self.fraud_case_repo = fraud_case_repo

    async def create_case(self, case_data: dict) -> FraudCase:
        """
        Create a new fraud case.

        Args:
            case_data: Case creation data

        Returns:
            Created case
        """
        case = FraudCase(**case_data)
        self.fraud_case_repo.session.add(case)
        await self.fraud_case_repo.session.flush()
        await self.fraud_case_repo.session.refresh(case)
        return case

    async def get_case(self, case_id: str) -> Optional[FraudCase]:
        """Get fraud case by ID."""
        return await self.fraud_case_repo.get(case_id)

    async def assign_investigator(
        self,
        case_id: str,
        investigator_id: str
    ) -> Optional[FraudCase]:
        """Assign investigator to case."""
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.investigator_id = investigator_id
        case.status = CaseStatus.UNDER_INVESTIGATION
        case.opened_at = datetime.now()

        await self.fraud_case_repo.session.flush()
        await self.fraud_case_repo.session.refresh(case)
        return case

    async def update_case_status(
        self,
        case_id: str,
        status: CaseStatus
    ) -> Optional[FraudCase]:
        """Update case status."""
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.status = status


        if status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]:
            case.closed_at = datetime.now()

        await self.fraud_case_repo.session.flush()
        await self.fraud_case_repo.session.refresh(case)
        return case

    async def close_case(
        self,
        case_id: str,
        fraud_confirmed: bool,
        resolution: str,
        summary: str
    ) -> Optional[FraudCase]:
        """Close fraud case with resolution."""
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.status = CaseStatus.CLOSED
        case.fraud_confirmed = fraud_confirmed
        case.resolution = resolution
        case.summary = summary
        case.closed_at = datetime.now()

        await self.fraud_case_repo.session.flush()
        await self.fraud_case_repo.session.refresh(case)
        return case
