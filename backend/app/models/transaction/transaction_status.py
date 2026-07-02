"""
TransactionStatus reference entity.

Represents the lifecycle state of a financial transaction.
Tracks the current state in the transaction workflow.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class TransactionStatusModel(Base, UUIDMixin, TimestampMixin):
    """
    Transaction status reference entity.
    
    Defines all possible states in a transaction lifecycle.
    This is a low-cardinality reference table.
    
    States: pending, processing, completed, failed, flagged, cancelled, refunded, reversed
    
    Attributes:
        code: Unique status code (e.g., 'pending', 'completed')
        name: Human-readable status name
        description: Detailed status description
        is_terminal: Whether this is an end state (no further transitions)
        sort_order: Display ordering
        is_active: Whether this status is currently in use
    """
    __tablename__ = "transaction_statuses"
    
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
    
    is_terminal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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
        back_populates="status_ref",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<TransactionStatus {self.code}>"