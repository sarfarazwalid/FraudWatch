"""
FraudRule model for configurable fraud detection rules.

Represents business rules that trigger fraud alerts based on transaction patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Boolean, Integer, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import DetectionMethod

if TYPE_CHECKING:
    from app.models.fraud.fraud_alert import FraudAlert


class FraudRule(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Configurable fraud detection rule.
    
    Represents a business rule used to detect fraudulent patterns in transactions.
    Rules can be based on thresholds, statistical analysis, or complex expressions.
    
    Design Rationale:
    - Versioned: Each rule has a version for audit and rollback
    - Reusable: Same rule can trigger multiple alerts
    - Toggleable: is_active enables/disables without deletion
    - Category-based: Organized by rule_category for management
    
    Attributes:
        rule_code: Unique business code for the rule (e.g., 'RULE_001')
        name: Human-readable rule name
        description: Detailed rule description and logic
        severity: Default severity for alerts triggered by this rule
        threshold: Numeric threshold value for rule activation
        rule_category: Category for grouping rules
        rule_expression: Rule logic expression (format TBD by implementation)
        is_active: Whether rule is currently active
        version: Rule version for audit trail
    """
    __tablename__ = "fraud_rules"
    
    # Identification
    rule_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique business code for the rule",
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable rule name",
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed rule description and logic",
    )
    
    # Configuration
    severity: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Default severity for alerts triggered by this rule",
    )
    
    threshold: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        doc="Numeric threshold for rule activation",
    )
    
    rule_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Category for grouping rules",
    )
    
    rule_expression: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Rule logic expression",
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether rule is currently active",
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Rule version for audit trail",
    )
    
    # Relationships
    alerts: Mapped[list["FraudAlert"]] = relationship(
        "FraudAlert",
        back_populates="rule",
        lazy="selectin",
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "threshold IS NULL OR threshold >= 0",
            name="ck_fraud_rules_threshold_positive",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_fraud_rules_version_positive",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<FraudRule {self.rule_code} v{self.version}>"