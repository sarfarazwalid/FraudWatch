"""
InvestigationTimeline Repository Implementation.

Data access layer for InvestigationTimeline model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional
from datetime import datetime

from app.models.fraud.investigation_timeline import InvestigationTimeline
from app.models.fraud.enums import TimelineActionType
from app.repositories.base import BaseRepository


class InvestigationTimelineRepository(BaseRepository[InvestigationTimeline, Any, Any]):
    """
    Repository for InvestigationTimeline model.

    Provides investigation timeline-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(InvestigationTimeline, session)

    async def get_by_case_id(self, case_id: str) -> List[InvestigationTimeline]:
        """Get all timeline entries for a case."""
        return await self.get_all(
            filters={"case_id": case_id, "deleted_at": None}
        )

    async def get_by_performed_by(self, performed_by: str) -> List[InvestigationTimeline]:
        """Get all timeline entries by a specific user."""
        return await self.get_all(
            filters={"performed_by": performed_by, "deleted_at": None}
        )

    async def get_by_action_type(
        self,
        action_type: TimelineActionType,
        skip: int = 0,
        limit: int = 100
    ) -> List[InvestigationTimeline]:
        """Get timeline entries by action type."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"action_type": action_type, "deleted_at": None}
        )

    async def get_recent_entries(
        self,
        since: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[InvestigationTimeline]:
        """Get timeline entries since a specific timestamp."""
        result = await self.session.execute(
            select(InvestigationTimeline).where(
                InvestigationTimeline.performed_at >= since,
                InvestigationTimeline.deleted_at.is_(None)
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
