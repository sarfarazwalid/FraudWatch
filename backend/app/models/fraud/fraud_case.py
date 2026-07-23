"""
FraudCase model for formal fraud investigations.

Represents a structured investigation workflow for a detected fraud alert.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import CasePriority, CaseStatus

if TYPE_CHECKING:
    from app.models.fraud.fraud_alert import FraudAlert
    from app.models.fraud.investigation_timeline import InvestigationTimeline
    from app.models.fraud.fraud_comment import FraudComment
    from app.models.fraud.fraud_attachment import FraudAttachment
    from app.models.identity.user import User
    from app.models.transaction.merchant import Merchant


class FraudCase(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Formal fraud investigation case.

    Represents a structured investigation workflow that tracks the complete
    lifecycle of a fraud investigation from creation to closure.

    Design Rationale:
    - Separate from Alert: Alert is detection, Case is investigation
    - Comprehensive: Links to timeline, comments, and evidence
    - Escalation support: escalation_level enables routing
    - Loss tracking: loss_amount for financial impact quantification

    Attributes:
        case_number: Unique case reference number (business key)
        alert_id: FK to originating alert
        priority: Investigation priority level
        status: Current investigation status
        investigator_id: FK to lead investigator
        opened_at: When investigation was opened
        closed_at: When investigation was closed
        escalation_level: Current escalation tier
        fraud_confirmed: Whether fraud was confirmed
        loss_amount: Financial loss amount (if confirmed)
        resolution: Resolution type/category
        summary: Investigation summary
    """
    __tablename__ = "fraud_cases"

    # Business Key
    case_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique case reference number",
    )

    # Foreign Keys
    alert_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("fraud_alerts.id", name="fk_fraud_cases_alert_id"),
        nullable=True,
        unique=True,
        index=True,
        doc="Originating fraud alert",
    )

    investigator_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_fraud_cases_investigator_id"),
        nullable=True,
        index=True,
        doc="Lead investigator assigned to case",
    )

    # Foreign Keys
    merchant_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("merchants.id", name="fk_fraud_cases_merchant_id"),
        nullable=True,
        index=True,
        doc="Related merchant",
    )

    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_fraud_cases_assigned_to_user"),
        nullable=True,
        index=True,
        doc="User assigned to investigate",
    )

    # Classification
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        index=True,
        doc="Case severity level",
    )

    priority: Mapped[CasePriority] = mapped_column(
        nullable=False,
        default=CasePriority.MEDIUM,
        index=True,
        doc="Investigation priority level",
    )

    status: Mapped[CaseStatus] = mapped_column(
        nullable=False,
        default=CaseStatus.NEW,
        index=True,
        doc="Current investigation status",
    )

    escalation_level: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        doc="Escalation tier (0 = no escalation)",
    )

    # Investigation Details
    opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When investigation was opened",
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When investigation was closed",
    )

    fraud_confirmed: Mapped[Optional[bool]] = mapped_column(
        nullable=True,
        doc="Whether fraud was confirmed",
    )

    loss_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Financial loss amount",
    )

    resolution: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Resolution category",
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Investigation summary",
    )

    # Relationships
    # Note: alert relationship is accessed through FraudAlert.case

    investigator: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[investigator_id],
    )

    assigned_user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[assigned_to],
    )

    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        lazy="selectin",
    )

    timeline_entries: Mapped[list["InvestigationTimeline"]] = relationship(
        "InvestigationTimeline",
        back_populates="case",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="InvestigationTimeline.performed_at.desc()",
    )

    comments: Mapped[list["FraudComment"]] = relationship(
        "FraudComment",
        back_populates="case",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="FraudComment.created_at.desc()",
    )

    attachments: Mapped[list["FraudAttachment"]] = relationship(
        "FraudAttachment",
        back_populates="case",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="FraudAttachment.uploaded_at.desc()",
    )

    # Constraints
    __table_args__ = (
        Index("ix_fraud_cases_status_priority", "status", "priority"),
        Index("ix_fraud_cases_investigator_status", "investigator_id", "status"),
        Index("ix_fraud_cases_severity", "severity"),
        Index("ix_fraud_cases_merchant", "merchant_id"),
        CheckConstraint(
            "escalation_level >= 0",
            name="ck_fraud_cases_escalation_level_positive",
        ),
        CheckConstraint(
            "loss_amount IS NULL OR loss_amount >= 0",
            name="ck_fraud_cases_loss_amount_positive",
        ),
    )

    def __repr__(self) -> str:
        return f"<FraudCase {self.case_number} status={self.status}>"
