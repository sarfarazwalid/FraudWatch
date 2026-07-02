"""
UserSession model for tracking active user sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID as PyUUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
)
from app.models.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.identity.user import User


class UserSession(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    User session model for tracking active sessions.
    """
    __tablename__ = "user_sessions"
    
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_user_sessions_user_id"),
        nullable=False,
        index=True,
    )
    
    session_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    status: Mapped[SessionStatus] = mapped_column(
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
    )
    
    device_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    device_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    browser: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    os: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )
    
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    user: Mapped[User] = relationship(
        "User",
        back_populates="sessions",
    )
    
    def __repr__(self) -> str:
        return f"<UserSession {self.session_token[:8]}...>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired