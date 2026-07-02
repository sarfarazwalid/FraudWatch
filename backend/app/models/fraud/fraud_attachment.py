"""
FraudAttachment model for storing attachment metadata.

Never stores binary files - only metadata about files stored in object storage.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.fraud.fraud_case import FraudCase
    from app.models.identity.user import User


class FraudAttachment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Fraud investigation attachment metadata.
    
    Stores metadata about files attached to fraud cases.
    Binary files are stored in external object storage (S3, GCS, etc.).
    
    Design Rationale:
    - Metadata-only: Database stores only file metadata
    - Separate storage: Binary files in S3/GCS/Azure Blob
    - Checksummed: Integrity verification
    - Tracked: Complete audit trail
    
    Attributes:
        case_id: FK to investigation case
        uploaded_by: FK to user who uploaded
        file_name: Original filename
        mime_type: File MIME type
        file_size: File size in bytes
        storage_path: Path in object storage
        checksum: File integrity checksum (SHA-256)
        uploaded_at: When file was uploaded
    """
    __tablename__ = "fraud_attachments"
    
    # Foreign Keys
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("fraud_cases.id", name="fk_fraud_attachments_case_id"),
        nullable=False,
        index=True,
        doc="Investigation case",
    )
    
    uploaded_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", name="fk_fraud_attachments_uploaded_by"),
        nullable=True,
        index=True,
        doc="User who uploaded file",
    )
    
    # File Details
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original filename",
    )
    
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="File MIME type",
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="File size in bytes",
    )
    
    # Storage
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Path in object storage",
    )
    
    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA-256 checksum for integrity verification",
    )
    
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When file was uploaded",
    )
    
    # Relationships
    case: Mapped["FraudCase"] = relationship(
        "FraudCase",
        back_populates="attachments",
        lazy="selectin",
    )
    
    uploaded_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[uploaded_by],
    )
    
    # Constraints
    __table_args__ = (
        Index("ix_fraud_attachments_case_uploaded", "case_id", "uploaded_at"),
        Index("ix_fraud_attachments_uploader_uploaded", "uploaded_by", "uploaded_at"),
        # Ensure checksum is always present (integrity)
    )
    
    def __repr__(self) -> str:
        return f"<FraudAttachment {self.id} file={self.file_name}>"