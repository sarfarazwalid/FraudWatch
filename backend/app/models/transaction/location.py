"""
Location entity.

Represents geographic location data for transactions.
Supports fraud detection through geolocation and IP analysis.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class Location(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Location entity.
    
    Stores geographic and network location data for transactions.
    Used by fraud detection to identify anomalous location patterns.
    
    Attributes:
        country: ISO 3166-1 alpha-2 country code
        division: State, province, or division
        district: District or county
        city: City name
        postal_code: Postal or ZIP code
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
        timezone: IANA timezone (e.g., 'Asia/Dhaka')
    """
    __tablename__ = "locations"
    
    country: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        index=True,
    )
    
    division: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8),
        nullable=True,
    )
    
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(11, 8),
        nullable=True,
    )
    
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="location",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Location {self.country}/{self.city}>"