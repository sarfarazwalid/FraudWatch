"""
FraudAlert Repository Implementation.

Data access layer for FraudAlert model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional
from datetime import datetime

from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.enums import AlertStatus, AlertSeverity
from app.repositories.base import BaseRepository


class FraudAlertRepository(BaseRepository[FraudAlert, Any, Any]):
    """
    Repository for FraudAlert model.

    Provides fraud alert-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(FraudAlert, session)

    async def get_by_alert_number(self, alert_number: str) -> Optional[FraudAlert]:
        """Get fraud alert by alert number."""
        return await self.get_by_field("alert_number", alert_number)

    async def get_by_transaction_id(self, transaction_id: str) -> List[FraudAlert]:
        """Get all alerts for a specific transaction."""
        return await self.get_all(filters={"transaction_id": transaction_id, "deleted_at": None})

    async def get_alerts_by_status(
        self,
        status: AlertStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get alerts by status."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"status": status, "deleted_at": None}
        )

    async def get_alerts_by_severity(
        self,
        severity: AlertSeverity,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get alerts by severity level."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"severity": severity, "deleted_at": None}
        )

    async def get_pending_alerts(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get alerts that need attention (new or acknowledged)."""
        result = await self.session.execute(
            select(FraudAlert).where(
                FraudAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]),
                FraudAlert.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_critical_alerts(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get critical severity alerts."""
        return await self.get_alerts_by_severity(AlertSeverity.CRITICAL, skip, limit)

    async def count_by_status(self, status: AlertStatus) -> int:
        """Count alerts by status."""
        result = await self.session.execute(
            select(func.count()).select_from(FraudAlert).where(
                FraudAlert.status == status,
                FraudAlert.deleted_at.is_(None)
            )
        )
        return result.scalar_one()

    async def get_alerts_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[FraudAlert]:
        """Get alerts within a date range."""
        result = await self.session.execute(
            select(FraudAlert).where(
                FraudAlert.generated_at >= start_date,
                FraudAlert.generated_at <= end_date,
                FraudAlert.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
