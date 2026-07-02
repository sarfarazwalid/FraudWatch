"""
Alembic environment configuration for FraudWatch.

This module configures Alembic for database migrations with:
- Online and offline migration support
- Async compatibility
- Environment-aware configuration
- Enterprise naming conventions
- Comprehensive model metadata
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any, Optional

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Alembic configuration
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models for autogenerate
from app.models.base import Base
from app.models.mixins import BaseModel
from app.models.enums import (
    UserStatus, RoleType, PermissionAction, SessionStatus, TokenType,
    AuthenticationProvider, TransactionStatusValue, RiskLevelValue,
    TransactionChannel, SourceSystem
)
from app.models.identity import (
    User, Role, Permission, RolePermission, UserSession, RefreshToken
)
from app.models.transaction import (
    Currency, PaymentMethod, TransactionType, TransactionStatusModel,
    RiskLevelCode, Merchant, Agent, Device, Location, Transaction
)
from app.models.fraud import (
    FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
    RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment
)
from app.models.fraud.enums import (
    AlertSeverity, AlertStatus, CasePriority, CaseStatus, DetectionMethod,
    PredictionLabel, RiskDecision, TimelineActionType, CommentVisibility,
    AttachmentType, ExplanationMethod
)
from app.models.ml import (
    DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
    FeatureImportance, PredictionHistory, ModelRegistry
)
from app.models.ml.enums import (
    TrainingStatus, ModelStatus, DeploymentEnvironment, PredictionStatus,
    AlgorithmType, FrameworkType, DatasetSource
)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get database URL from environment or settings.
    
    Supports environment-aware configuration:
    - DEVELOPMENT: Local PostgreSQL
    - TESTING: PostgreSQL test database
    - PRODUCTION: Production PostgreSQL
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Try to import settings
    try:
        from app.config.settings import settings
        return settings.database_sync_url
    except ImportError:
        pass
    
    # Fallback to environment variables
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Default for development
    if environment == "development":
        return "postgresql://fraudwatch:fraudwatch@localhost:5432/fraudwatch_dev"
    elif environment == "testing":
        return "postgresql://fraudwatch:fraudwatch@localhost:5432/fraudwatch_test"
    elif environment == "production":
        return os.getenv("DATABASE_URL_PROD", "")
    
    raise ValueError(f"No database URL configured for environment: {environment}")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
        named_transient_migrations=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Any) -> None:
    """
    Run migrations with connection.
    
    Args:
        connection: Database connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
        named_transient_migrations=True,
        # Process ENUM types
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def process_revision_directives(context: Any, revision: Any, directives: Any) -> None:
    """
    Custom revision directive processor.
    
    Can be used to customize migration generation.
    """
    # Auto-generate migration if there are changes
    # if directives and len(directives) > 0:
    #     directive = directives[0]
    #     # Customize migration message
    #     pass
    pass


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Creates an Engine and associates a connection with the context.
    """
    database_url = get_database_url()
    
    # Check if using async driver
    if database_url.startswith("postgresql+asyncpg://"):
        # Convert to sync URL for Alembic
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        config.set_main_option("sqlalchemy.url", sync_url)
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)
    
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()