"""
FraudAlert service.

Handles fraud alert business logic and escalation workflows.
"""

from typing import Optional, List
from datetime import datetime

from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.enums import AlertStatus, AlertSeverity
from app.repositories.fraud_alert import FraudAlertRepository


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
