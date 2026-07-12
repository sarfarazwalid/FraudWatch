"""
UserRole junction table for many-to-many relationship between users and roles.

This is an association table that links users to their roles.
"""

from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.mixins import UUIDMixin


class UserRole(Base, UUIDMixin):
    """
    Junction table for User-Role many-to-many relationship.

    Note: The schema uses a composite primary key (user_id, role_id)
    but for SQLAlchemy ORM, we use a single UUID id column.
    """
    __tablename__ = "user_roles"

    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    assigned_by: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
