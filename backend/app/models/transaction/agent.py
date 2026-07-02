"""
Agent entity.

Represents mobile wallet agents or field agents who facilitate transactions
for customers. Common in mobile money ecosystems like bKash, Nagad.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.transaction.transaction import Transaction


class Agent(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin):
    """
    Agent entity.
    
    Represents field agents who facilitate transactions for end customers.
    Common in mobile money ecosystems (bKash, Nagad, etc.).
    
    Attributes:
        agent_code: Unique agent identifier
        agent_name: Full name of the agent
        branch_name: Branch or outlet name
        district: Geographic district of operation
        status: Current agent status (active, inactive, suspended)
        commission_rate: Commission percentage for facilitated transactions
        is_active: Whether agent is currently active
    """
    __tablename__ = "agents"
    
    agent_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    agent_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    branch_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="active",
        index=True,
    )
    
    commission_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4),
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
        back_populates="agent",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Agent {self.agent_code}>"