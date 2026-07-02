"""
Transaction entity - Core domain model.

Represents a financial transaction ingested from external payment systems.
This is the central entity in the FraudWatch platform.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.enums import TransactionChannel, SourceSystem

if TYPE_CHECKING:
    from app.models.transaction.currency import Currency
    from app.models.transaction.payment_method import PaymentMethod
    from app.models.transaction.transaction_type import TransactionType
    from app.models.transaction.transaction_status import TransactionStatusModel
    from app.models.transaction.risk_level import RiskLevelCode
    from app.models.transaction.merchant import Merchant
    from app.models.transaction.agent import Agent
    from app.models.transaction.device import Device
    from app.models.transaction.location import Location


class Transaction(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Core transaction entity.
    
    Represents a financial transaction ingested from an external payment system.
    This is the central entity that fraud detection, risk assessment, and
    investigation workflows operate on.
    
    Design Rationale:
    - Normalized: References to merchant, agent, device, location via FKs
    - Immutable: Core financial fields (amount, fee) never change after creation
    - Status-driven: State machine via status_ref FK
    - Extensible: JSONB metadata for system-specific fields
    - Partition-ready: transaction_timestamp enables monthly partitioning
    
    Attributes:
        transaction_reference: Internal unique transaction reference
        external_reference: External system's transaction ID
        sender_identifier: Sender account/wallet/phone identifier
        receiver_identifier: Receiver account/wallet/phone identifier
        merchant_id: FK to merchant (if merchant payment)
        agent_id: FK to agent (if agent-facilitated)
        device_id: FK to device (if tracked)
        location_id: FK to location (if geolocated)
        currency_id: FK to currency
        payment_method_id: FK to payment method
        transaction_type_id: FK to transaction type
        status_id: FK to transaction status
        risk_level_id: FK to risk level (nullable, set by ML)
        amount: Transaction amount in currency units
        fee: Fee charged for the transaction
        net_amount: amount - fee (computed)
        exchange_rate: Exchange rate if multi-currency
        transaction_timestamp: When the transaction occurred
        channel: Origination channel (mobile_app, web, ussd, etc.)
        source_system: External system that originated the transaction
        description: Human-readable transaction description
        transaction_metadata: JSONB for extensible system-specific data
    """
    __tablename__ = "transactions"
    
    # Identifiers
    transaction_reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Party identifiers
    sender_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    receiver_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Foreign Keys
    merchant_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("merchants.id", name="fk_transactions_merchant_id"),
        nullable=True,
        index=True,
    )
    
    agent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("agents.id", name="fk_transactions_agent_id"),
        nullable=True,
        index=True,
    )
    
    device_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("devices.id", name="fk_transactions_device_id"),
        nullable=True,
        index=True,
    )
    
    location_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("locations.id", name="fk_transactions_location_id"),
        nullable=True,
        index=True,
    )
    
    currency_id: Mapped[UUID] = mapped_column(
        ForeignKey("currencies.id", name="fk_transactions_currency_id"),
        nullable=False,
    )
    
    payment_method_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_methods.id", name="fk_transactions_payment_method_id"),
        nullable=False,
    )
    
    transaction_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("transaction_types.id", name="fk_transactions_transaction_type_id"),
        nullable=False,
    )
    
    status_id: Mapped[UUID] = mapped_column(
        ForeignKey("transaction_statuses.id", name="fk_transactions_status_id"),
        nullable=False,
        index=True,
    )
    
    risk_level_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("risk_levels.id", name="fk_transactions_risk_level_id"),
        nullable=True,
        index=True,
    )
    
    # Financial fields
    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    
    fee: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0.00,
    )
    
    net_amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    
    exchange_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 8),
        nullable=True,
    )
    
    # Temporal
    transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    # Classification
    channel: Mapped[Optional[TransactionChannel]] = mapped_column(
        nullable=True,
    )
    
    source_system: Mapped[Optional[SourceSystem]] = mapped_column(
        nullable=True,
    )
    
    # Descriptive
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Extensible data
    transaction_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Relationships
    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        back_populates="transactions",
        lazy="selectin",
    )
    
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="transactions",
        lazy="selectin",
    )
    
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="transactions",
        lazy="selectin",
    )
    
    location: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="transactions",
        lazy="selectin",
    )
    
    currency: Mapped["Currency"] = relationship(
        "Currency",
        back_populates="transactions",
        lazy="selectin",
    )
    
    payment_method: Mapped["PaymentMethod"] = relationship(
        "PaymentMethod",
        back_populates="transactions",
        lazy="selectin",
    )
    
    transaction_type: Mapped["TransactionType"] = relationship(
        "TransactionType",
        back_populates="transactions",
        lazy="selectin",
    )
    
    status_ref: Mapped["TransactionStatusModel"] = relationship(
        "TransactionStatusModel",
        back_populates="transactions",
        lazy="selectin",
    )
    
    risk_level_ref: Mapped[Optional["RiskLevelCode"]] = relationship(
        "RiskLevelCode",
        back_populates="transactions",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Transaction ref={self.transaction_reference}>"