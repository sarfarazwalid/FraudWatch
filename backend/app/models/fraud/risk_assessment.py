"""
RiskAssessment model for aggregated risk evaluation.

Stores comprehensive risk scores from multiple detection sources.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import RiskDecision

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class RiskAssessment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Aggregated risk evaluation for a transaction.
    
    Combines scores from multiple risk sources into a unified assessment.
    Used for real-time risk decisions and model monitoring.
    
    Design Rationale:
    - Multi-source: Combines rule, ML, behavior, velocity, geolocation, device
    - Decision-driven: Explicit decision field for action
    - Time-series: Partition-ready for historical analysis
    - Model-agnostic: Can incorporate new risk sources
    
    Attributes:
        transaction_id: FK to transaction being assessed
        overall_risk_score: Combined overall risk score (0-100)
        rule_score: Risk score from rule-based detection
        ml_score: Risk score from ML model
        behavior_score: Risk score from behavioral analysis
        velocity_score: Risk score from velocity checks
        geolocation_score: Risk score from geolocation analysis
        device_score: Risk score from device fingerprinting
        decision: Risk decision (approve/review/reject/block/escalate)
        assessed_at: When assessment was performed
    """
    __tablename__ = "risk_assessments"
    
    # Foreign Keys
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", name="fk_risk_assessments_transaction_id"),
        nullable=False,
        index=True,
        doc="Transaction being assessed",
    )
    
    # Risk Scores
    overall_risk_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Combined overall risk score (0-100)",
    )
    
    rule_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Risk score from rule-based detection",
    )
    
    ml_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Risk score from ML model (0-1)",
    )
    
    behavior_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Risk score from behavioral analysis",
    )
    
    velocity_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Risk score from velocity checks",
    )
    
    geolocation_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Risk score from geolocation analysis",
    )
    
    device_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Risk score from device fingerprinting",
    )
    
    # Decision
    decision: Mapped[RiskDecision] = mapped_column(
        nullable=False,
        index=True,
        doc="Risk decision",
    )
    
    assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When assessment was performed",
    )
    
    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        lazy="selectin",
        foreign_keys=[transaction_id],
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_risk_assessments_transaction_assessed", "transaction_id", "assessed_at"),
        CheckConstraint(
            "overall_risk_score IS NULL OR (overall_risk_score >= 0 AND overall_risk_score <= 100)",
            name="ck_risk_assessments_overall_score_range",
        ),
        CheckConstraint(
            "rule_score IS NULL OR (rule_score >= 0 AND rule_score <= 100)",
            name="ck_risk_assessments_rule_score_range",
        ),
        CheckConstraint(
            "ml_score IS NULL OR (ml_score >= 0 AND ml_score <= 1)",
            name="ck_risk_assessments_ml_score_range",
        ),
        CheckConstraint(
            "behavior_score IS NULL OR (behavior_score >= 0 AND behavior_score <= 100)",
            name="ck_risk_assessments_behavior_score_range",
        ),
        CheckConstraint(
            "velocity_score IS NULL OR (velocity_score >= 0 AND velocity_score <= 100)",
            name="ck_risk_assessments_velocity_score_range",
        ),
        CheckConstraint(
            "geolocation_score IS NULL OR (geolocation_score >= 0 AND geolocation_score <= 100)",
            name="ck_risk_assessments_geolocation_score_range",
        ),
        CheckConstraint(
            "device_score IS NULL OR (device_score >= 0 AND device_score <= 100)",
            name="ck_risk_assessments_device_score_range",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<RiskAssessment {self.id} decision={self.decision}>"