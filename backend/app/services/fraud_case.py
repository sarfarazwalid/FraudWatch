"""
FraudCase service.

Handles fraud investigation case business logic and workflow management.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.enums import CaseStatus, CasePriority
from app.repositories.fraud_case import FraudCaseRepository
from sqlalchemy import select, or_, and_


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

    async def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[FraudCase], int]:
        """
        Get paginated, filtered, and sorted fraud cases.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for case_number, title, description
            filters: Dictionary of field filters (status, severity, assigned_to, merchant_id)
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (items, total_count)
        """
        # Build base query
        query = select(FraudCase)
        count_query = select(FraudCase.id)

        # Apply search filter
        conditions = []
        if search:
            conditions.append(or_(
                FraudCase.case_number.ilike(f"%{search}%"),
                FraudCase.title.ilike(f"%{search}%"),
                FraudCase.description.ilike(f"%{search}%"),
            ))

        # Apply filters
        if filters:
            if "status" in filters and filters["status"]:
                conditions.append(FraudCase.status == filters["status"])
            if "severity" in filters and filters["severity"]:
                conditions.append(FraudCase.severity == filters["severity"])
            if "assigned_to" in filters and filters["assigned_to"]:
                conditions.append(FraudCase.assigned_to == filters["assigned_to"])
            if "merchant_id" in filters and filters["merchant_id"]:
                conditions.append(FraudCase.merchant_id == filters["merchant_id"])

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.fraud_case_repo.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Apply sorting
        sort_field = getattr(FraudCase, sort_by, FraudCase.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.fraud_case_repo.session.execute(query)
        items = list(result.scalars().all())

        return items, total

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
