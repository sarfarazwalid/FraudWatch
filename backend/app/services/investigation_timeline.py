"""
InvestigationTimeline service.

Handles investigation timeline business logic.
"""

from typing import Optional, List
from datetime import datetime

from app.models.fraud.investigation_timeline import InvestigationTimeline
from app.models.fraud.enums import TimelineActionType
from app.repositories.investigation_timeline import InvestigationTimelineRepository


class InvestigationTimelineService:
    """
    Service for investigation timeline operations.

    Handles timeline entry creation and retrieval.
    """

    def __init__(self, investigation_timeline_repo: InvestigationTimelineRepository):
        self.investigation_timeline_repo = investigation_timeline_repo

    async def create_timeline_entry(self, entry_data: dict) -> InvestigationTimeline:
        """
        Create a new timeline entry.

        Args:
            entry_data: Timeline entry data

        Returns:
            Created timeline entry
        """
        entry = InvestigationTimeline(**entry_data)
        self.investigation_timeline_repo.session.add(entry)
        await self.investigation_timeline_repo.session.flush()
        await self.investigation_timeline_repo.session.refresh(entry)
        return entry

    async def get_timeline_entry(self, entry_id: str) -> Optional[InvestigationTimeline]:
        """Get timeline entry by ID."""
        return await self.investigation_timeline_repo.get(entry_id)

    async def get_case_timeline(self, case_id: str) -> List[InvestigationTimeline]:
        """Get all timeline entries for a case."""
        return await self.investigation_timeline_repo.get_by_case_id(case_id)

    async def get_entries_by_action_type(
        self,
        action_type: TimelineActionType,
        skip: int = 0,
        limit: int = 100
    ) -> List[InvestigationTimeline]:
        """Get timeline entries by action type."""
        return await self.investigation_timeline_repo.get_by_action_type(action_type, skip, limit)
