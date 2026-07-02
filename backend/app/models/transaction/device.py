"""
Device entity.

Represents customer device information used for transaction tracking
and fraud detection. Includes device fingerprinting data.
"""

from typing import TYPE_CHECKING, Optional

from datetime import datetime

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class Device(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Device entity.
    
    Tracks device information for transactions to support fraud detection
    through device profiling and anomaly detection.
    
    Attributes:
        device_identifier: Unique device identifier (platform-specific)
        device_fingerprint: Browser/device fingerprint hash
        manufacturer: Device manufacturer (e.g., 'Samsung', 'Apple')
        model: Device model (e.g., 'Galaxy S24', 'iPhone 15')
        operating_system: OS name and version (e.g., 'Android 14', 'iOS 17')
        browser: Browser name and version
        app_version: Application version if from mobile app
        ip_address: IP address associated with the device
        user_agent: Raw user agent string
        trusted: Whether device has been marked as trusted
        last_seen: Timestamp of last activity from this device
    """
    __tablename__ = "devices"
    
    device_identifier: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    device_fingerprint: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    operating_system: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    browser: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    app_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    trusted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="device",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Device fingerprint={self.device_fingerprint[:12]}...>"