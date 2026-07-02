"""
FraudComment model for analyst collaboration.

Allows multiple analysts to collaborate on fraud investigations.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
from app.models.fraud.enums import CommentVisibility

if TYPE_CHECKING:
    from app.models.fraud.fraud_case import FraudCase
    from app.models.identity.user import User


class FraudComment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Fraud investigation comment.
    
    Enables analyst collaboration on case investigations.
    Comments are stored separately from cases to maintain normalization.
    
    Design Rationale:
    - Separate from Case: Avoids bloating case table
    - Editable: edited/edited_at tracks modifications
    - Visibility-controlled: Internal/external/restricted
    - Rich text: Supports detailed investigation notes
    
    Attributes:
        case_id: FK to investigation case
        author_id: FK to comment author
        comment: Comment text content
        visibility: Comment visibility level
        edited: Whether comment was edited
        edited_at: When comment was last edited
    """
    __tablename__ = "fraud_comments"
    
    # Foreign Keys
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("fraud_cases.id", name="fk_fraud_comments_case_id"),
        nullable=False,
        index=True,
        doc="Investigation case",
    )
    
    author_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_fraud_comments_author_id"),
        nullable=True,
        index=True,
        doc="Comment author",
    )
    
    # Content
    comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Comment text content",
    )
    
    visibility: Mapped[CommentVisibility] = mapped_column(
        nullable=False,
        default=CommentVisibility.INTERNAL,
        index=True,
        doc="Comment visibility level",
    )
    
    # Edit Tracking
    edited: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        doc="Whether comment was edited",
    )
    
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When comment was last edited",
    )
    
    # Relationships
    case: Mapped["FraudCase"] = relationship(
        "FraudCase",
        back_populates="comments",
        lazy="selectin",
    )
    
    author: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[author_id],
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_fraud_comments_case_created", "case_id", "created_at"),
        Index("ix_fraud_comments_author_created", "author_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<FraudComment {self.id} case={self.case_id}>"