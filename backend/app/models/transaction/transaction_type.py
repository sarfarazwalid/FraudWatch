"""
TransactionType reference entity.

Represents the type/category of a financial transaction.
Examples: Cash In, Cash Out, P2P Transfer, Merchant Payment, etc.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class TransactionType(Base, UUIDMixin, TimestampMixin):
    """
    Transaction type reference entity.
    
    Categorizes the nature of a financial transaction.
    This is a low-cardinality reference table.
    
    Examples:
        - Cash In
        - Cash Out
        - P2P Transfer
        - Merchant Payment
        - Bill Payment
        - Refund
        - Reversal
        - Adjustment
    
    Attributes:
        name: Display name of the transaction type
        description: Detailed description
        is_active: Whether this type is currently supported
    """
    __tablename__ = "transaction_types"
    
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="transaction_type",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<TransactionType {self.name}>"