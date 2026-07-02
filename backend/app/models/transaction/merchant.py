"""
Merchant entity.

Represents a business or entity that accepts payments via the platform.
Merchants are the counterparty in merchant payment transactions.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class Merchant(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Merchant entity.
    
    Represents businesses registered on the platform to accept payments.
    Each merchant has a unique code and risk assessment.
    
    Attributes:
        merchant_code: Unique business identifier
        merchant_name: Registered business name
        merchant_category: MCC or business category code
        registration_number: Government business registration
        business_type: Type of business (e.g., retail, service, utility)
        risk_rating: Internal risk assessment rating
        status: Current merchant status (active, suspended, terminated)
        email: Primary contact email
        phone: Primary contact phone
        website: Business website URL
        is_active: Whether merchant is currently active
    """
    __tablename__ = "merchants"
    
    merchant_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    merchant_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    merchant_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    registration_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    business_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    risk_rating: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="active",
        index=True,
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    website: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="merchant",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Merchant {self.merchant_code}>"