"""
InvestigationTimeline model for audit trail.

Stores every analyst action in an append-only timeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import TimelineActionType

if TYPE_CHECKING:
    from app.models.fraud.fraud_case import FraudCase
    from app.models.identity.user import User


class InvestigationTimeline(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Append-only investigation timeline entry.
    
    Records every analyst action during fraud investigation.
    Nothing should be deleted from this table - it's a complete audit trail.
    
    Design Rationale:
    - Append-only: Never deleted, only inserted
    - Comprehensive: Captures all state changes
    - Actor-tracked: Links to user who performed action
    - Timestamped: Precise action timing
    
    Attributes:
        case_id: FK to investigation case
        performed_by: FK to user who performed action
        action_type: Type of action performed
        previous_status: Case status before action
        new_status: Case status after action
        notes: Additional details about action
        performed_at: When action was performed
    """
    __tablename__ = "investigation_timeline"
    
    # Foreign Keys
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("fraud_cases.id", name="fk_investigation_timeline_case_id"),
        nullable=False,
        index=True,
        doc="Investigation case",
    )
    
    performed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_investigation_timeline_performed_by"),
        nullable=True,
        index=True,
        doc="User who performed action",
    )
    
    # Action Details
    action_type: Mapped[TimelineActionType] = mapped_column(
        nullable=False,
        index=True,
        doc="Type of action performed",
    )
    
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Case status before action",
    )
    
    new_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Case status after action",
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional details about action",
    )
    
    performed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When action was performed",
    )
    
    # Relationships
    case: Mapped["FraudCase"] = relationship(
        "FraudCase",
        back_populates="timeline_entries",
        lazy="selectin",
    )
    
    performed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[performed_by],
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_investigation_timeline_case_performed", "case_id", "performed_at"),
        Index("ix_investigation_timeline_user_performed", "performed_by", "performed_at"),
        Index("ix_investigation_timeline_action_performed", "action_type", "performed_at"),
    )
    
    def __repr__(self) -> str:
        return f"<InvestigationTimeline {self.id} action={self.action_type}>"