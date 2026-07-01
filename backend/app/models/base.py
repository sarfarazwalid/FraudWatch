"""
Base model for all SQLAlchemy ORM models.

Provides the foundational DeclarativeBase class that all models inherit from.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Naming convention for constraints (indexes, foreign keys, etc.)
# This ensures consistent naming across migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base declarative class for all ORM models.
    
    All models should inherit from this class. It provides:
    - Automatic table naming
    - Metadata with naming convention
    - Common query methods (to be added via mixins)
    """
    metadata = MetaData(naming_convention=convention)
    
    # Default schema (can be overridden per model)
    __table_args__ = {"schema": "public"}