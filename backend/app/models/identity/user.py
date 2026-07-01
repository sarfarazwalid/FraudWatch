"""
User model for identity and access management.

Represents a platform user (fraud analyst, admin, compliance officer, etc.).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)
from app.models.enums import UserStatus


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    User model for platform users.
    """
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    status: Mapped[UserStatus] = mapped_column(
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    last_login: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="UTC",
    )
    
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default="en",
    )
    
    profile_image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until