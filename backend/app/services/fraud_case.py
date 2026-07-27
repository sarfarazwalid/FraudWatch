"""
FraudCase service.

Handles fraud investigation case business logic and workflow management.
"""

import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.enums import CaseStatus, CasePriority
from app.repositories.fraud_case import FraudCaseRepository
from app.schemas.fraud import PredictionResponse, RuleEvaluationResponse, AlertResponse, CaseResponse


class FraudCaseService:
    """
    Service for fraud case operations.

    Handles case creation, investigator assignment, and status transitions.
    """

    def __init__(self, fraud_case_repo: Optional[FraudCaseRepository] = None, session: Optional[AsyncSession] = None):
        self.fraud_case_repo = fraud_case_repo
        self.session = session or (fraud_case_repo.session if fraud_case_repo else None)

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

    async def create_from_alert(
        self,
        alert: AlertResponse,
        prediction: PredictionResponse,
        rule_evaluations: RuleEvaluationResponse,
        current_user,
    ) -> CaseResponse:
        """
        Create a fraud case from an alert.

        Called automatically when risk_score >= 0.85.

        Args:
            alert: The alert that triggered case creation
            prediction: The prediction result
            rule_evaluations: Rule evaluation results
            current_user: The user who created the transaction

        Returns:
            CaseResponse with case details
        """
        # Map risk score to severity
        risk_score = prediction.risk_score
        if risk_score >= 0.95:
            severity = "critical"
        elif risk_score >= 0.9:
            severity = "high"
        else:
            severity = "medium"

        # Map risk score to priority
        if risk_score >= 0.95:
            priority = CasePriority.CRITICAL
        elif risk_score >= 0.9:
            priority = CasePriority.HIGH
        else:
            priority = CasePriority.MEDIUM

        # Collect triggered rule names
        triggered_rules = [
            r.rule_name for r in rule_evaluations.rules if r.triggered
        ]

        # Generate case number
        case_number = f"CASE-{uuid.uuid4().hex[:8].upper()}"

        # Build description
        description = (
            f"Automatically generated case for suspicious transaction. "
            f"Risk score: {risk_score:.2f}. "
            f"Prediction: {prediction.prediction}. "
            f"Confidence: {prediction.confidence:.2f}. "
            f"Triggered rules: {', '.join(triggered_rules) if triggered_rules else 'None'}. "
            f"Model: {prediction.model_version}."
        )

        case = FraudCase(
            case_number=case_number,
            alert_id=alert.id,
            severity=severity,
            priority=priority,
            status=CaseStatus.NEW,
            escalation_level=0,
            opened_at=datetime.now(timezone.utc),
            summary=description,
        )
        self.session.add(case)
        await self.session.flush()
        await self.session.refresh(case)

        # Update alert with case_id
        alert_obj_result = await self.session.execute(
            select(FraudAlert).where(FraudAlert.id == alert.id).limit(1)
        )
        alert_obj = alert_obj_result.scalar_one_or_none()
        if alert_obj:
            alert_obj.case_id = case.id
            await self.session.flush()

        return CaseResponse(
            id=str(case.id),
            case_number=case.case_number,
            severity=case.severity,
            status=case.status.value if hasattr(case.status, 'value') else str(case.status),
            alert_id=str(case.alert_id) if case.alert_id else None,
            transaction_id=str(alert.transaction_id) if alert.transaction_id else None,
            risk_score=risk_score,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

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
        if not self.session:
            raise RuntimeError("FraudCaseService has no session available")

        # Build base query
        query = select(FraudCase)
        count_query = select(func.count()).select_from(FraudCase)

        # Apply search filter
        conditions = []
        if search:
            conditions.append(or_(
                FraudCase.case_number.ilike(f"%{search}%"),
                FraudCase.summary.ilike(f"%{search}%"),
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
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_field = getattr(FraudCase, sort_by, FraudCase.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def assign_investigator(
        self,
        case_id: str,
        investigator_id: str
    ) -> Optional[FraudCase]:
        """Assign investigator to case."""
        if not self.fraud_case_repo or not self.session:
            raise RuntimeError("FraudCaseService has no repository or session available")
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.investigator_id = investigator_id
        case.status = CaseStatus.UNDER_INVESTIGATION
        case.opened_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(case)
        return case

    async def update_case_status(
        self,
        case_id: str,
        status: CaseStatus
    ) -> Optional[FraudCase]:
        """Update case status."""
        if not self.fraud_case_repo or not self.session:
            raise RuntimeError("FraudCaseService has no repository or session available")
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.status = status

        if status in [CaseStatus.RESOLVED, CaseStatus.CLOSED]:
            case.closed_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(case)
        return case

    async def close_case(
        self,
        case_id: str,
        fraud_confirmed: bool,
        resolution: str,
        summary: str
    ) -> Optional[FraudCase]:
        """Close fraud case with resolution."""
        if not self.fraud_case_repo or not self.session:
            raise RuntimeError("FraudCaseService has no repository or session available")
        case = await self.fraud_case_repo.get(case_id)
        if not case:
            return None

        case.status = CaseStatus.CLOSED
        case.fraud_confirmed = fraud_confirmed
        case.resolution = resolution
        case.summary = summary
        case.closed_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(case)
        return case
