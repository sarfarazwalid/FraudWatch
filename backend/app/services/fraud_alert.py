"""
FraudAlert service.

Handles fraud alert business logic and escalation workflows.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.enums import AlertStatus, AlertSeverity
from app.repositories.fraud_alert import FraudAlertRepository
from sqlalchemy import select, or_, and_


class FraudAlertService:
    """
    Service for fraud alert operations.

    Handles alert creation, status updates, and escalation to cases.
    """

    def __init__(self, fraud_alert_repo: FraudAlertRepository):
        self.fraud_alert_repo = fraud_alert_repo

    async def create_alert(self, alert_data: dict) -> FraudAlert:
        """
        Create a new fraud alert.

        Args:
            alert_data: Alert creation data

        Returns:
            Created alert
        """
        alert = FraudAlert(**alert_data)
        self.fraud_alert_repo.session.add(alert)
        await self.fraud_alert_repo.session.flush()
        await self.fraud_alert_repo.session.refresh(alert)
        return alert

    async def get_alert(self, alert_id: str) -> Optional[FraudAlert]:
        """Get fraud alert by ID."""
        return await self.fraud_alert_repo.get(alert_id)

    async def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[FraudAlert], int]:
        """
        Get paginated, filtered, and sorted fraud alerts.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for alert_number, title, description
            filters: Dictionary of field filters (severity, status, case_id, merchant_id)
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (items, total_count)
        """
        # Build base query
        query = select(FraudAlert)
        count_query = select(FraudAlert.id)

        # Apply search filter
        conditions = []
        if search:
            conditions.append(or_(
                FraudAlert.alert_number.ilike(f"%{search}%"),
                FraudAlert.title.ilike(f"%{search}%"),
                FraudAlert.description.ilike(f"%{search}%"),
            ))

        # Apply filters
        if filters:
            if "severity" in filters and filters["severity"]:
                conditions.append(FraudAlert.severity == filters["severity"])
            if "status" in filters and filters["status"]:
                conditions.append(FraudAlert.status == filters["status"])
            if "case_id" in filters and filters["case_id"]:
                conditions.append(FraudAlert.case_id == filters["case_id"])
            if "merchant_id" in filters and filters["merchant_id"]:
                conditions.append(FraudAlert.merchant_id == filters["merchant_id"])

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.fraud_alert_repo.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Apply sorting
        sort_field = getattr(FraudAlert, sort_by, FraudAlert.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.fraud_alert_repo.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def acknowledge_alert(self, alert_id: str, analyst_id: str) -> Optional[FraudAlert]:
        """Acknowledge a fraud alert."""
        alert = await self.fraud_alert_repo.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.assigned_analyst_id = analyst_id
        alert.acknowledged_at = datetime.now()

        await self.fraud_alert_repo.session.flush()
        await self.fraud_alert_repo.session.refresh(alert)
        return alert

    async def resolve_alert(
        self,
        alert_id: str,
        resolution: str,
        false_positive: bool = False
    ) -> Optional[FraudAlert]:
        """Resolve a fraud alert."""
        alert = await self.fraud_alert_repo.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolution_summary = resolution
        alert.false_positive = false_positive
        alert.resolved_at = datetime.now()

        await self.fraud_alert_repo.session.flush()
        await self.fraud_alert_repo.session.refresh(alert)
        return alert

    async def escalate_to_case(self, alert_id: str, case_data: dict) -> Optional[dict]:
        """
        Escalate alert to fraud case.

        Args:
            alert_id: Alert ID
            case_data: Case creation data

        Returns:
            Created case data or None
        """
        alert = await self.fraud_alert_repo.get(alert_id)
        if not alert:
            return None

        # Update alert status
        alert.status = AlertStatus.ESCALATED
        await self.fraud_alert_repo.session.flush()

        # Return case data for case service to create
        return {
            "alert_id": alert_id,
            **case_data
        }
