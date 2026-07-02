"""
Currency reference entity.

Represents a monetary currency (ISO 4217 standard).
Used as a lookup table for transaction currencies.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class Currency(Base, UUIDMixin, TimestampMixin):
    """
    Currency reference entity (ISO 4217).
    
    Stores supported currencies for transactions.
    This is a low-cardinality reference table.
    
    Attributes:
        code: ISO 4217 currency code (e.g., 'BDT', 'USD')
        name: Full currency name (e.g., 'Bangladeshi Taka')
        symbol: Currency symbol (e.g., '৳', '$')
        decimal_places: Number of decimal places (e.g., 2)
        is_active: Whether this currency is currently supported
    """
    __tablename__ = "currencies"
    
    code: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    symbol: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    
    decimal_places: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="currency",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Currency {self.code}>"