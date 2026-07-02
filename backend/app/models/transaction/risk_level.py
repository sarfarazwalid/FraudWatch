"""
RiskLevel reference entity.

Represents risk classification levels for transactions.
Used by the ML model scoring system.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class RiskLevelCode(Base, UUIDMixin, TimestampMixin):
    """
    Risk level classification reference entity.
    
    Defines risk tiers used to categorize transactions by fraud probability.
    This is a low-cardinality reference table.
    
    Levels: low, medium, high, critical
    
    Attributes:
        code: Unique risk level code (e.g., 'low', 'high')
        name: Human-readable name
        description: Detailed description
        score_min: Minimum fraud score for this level (inclusive)
        score_max: Maximum fraud score for this level (inclusive)
        color_hex: Color code for UI display (e.g., '#00FF00')
        sort_order: Display ordering
        is_active: Whether this level is currently in use
    """
    __tablename__ = "risk_levels"
    
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    score_min: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    score_max: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    
    color_hex: Mapped[Optional[str]] = mapped_column(
        String(7),
        nullable=True,
    )
    
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="risk_level_ref",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<RiskLevel {self.code}>"