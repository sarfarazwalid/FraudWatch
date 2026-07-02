"""
PaymentMethod reference entity.

Represents a payment method type accepted by the platform.
Examples: Wallet, Bank Transfer, Debit Card, Credit Card, Cash In, etc.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class PaymentMethod(Base, UUIDMixin, TimestampMixin):
    """
    Payment method reference entity.
    
    Categorizes how a transaction was funded or executed.
    This is a low-cardinality reference table.
    
    Examples:
        - Wallet
        - Bank Transfer
        - Debit Card
        - Credit Card
        - Cash In
        - Cash Out
        - Merchant Payment
        - Bill Payment
        - Mobile Recharge
    
    Attributes:
        name: Display name of the payment method
        description: Detailed description of the method
        is_active: Whether this method is currently supported
    """
    __tablename__ = "payment_methods"
    
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
        back_populates="payment_method",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PaymentMethod {self.name}>"