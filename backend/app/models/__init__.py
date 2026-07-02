"""
FraudWatch ORM Models Package.

This package contains all SQLAlchemy 2.x ORM models organized by domain.
"""

from app.models.base import Base
from app.models.mixins import (
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    VersionMixin,
    BaseModel,
)

# Identity domain
from app.models.identity import (
    User,
    Role,
    Permission,
    RolePermission,
    UserSession,
    RefreshToken,
)

# Transaction domain
from app.models.transaction import (
    Currency,
    PaymentMethod,
    TransactionType,
    TransactionStatusModel,
    RiskLevelCode,
    Merchant,
    Agent,
    Device,
    Location,
    Transaction,
)

# Fraud domain
from app.models.fraud import (
    FraudAlert,
    FraudCase,
    FraudRule,
    Prediction,
    PredictionExplanation,
    RiskAssessment,
    InvestigationTimeline,
    FraudComment,
    FraudAttachment,
)

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "VersionMixin",
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserSession",
    "RefreshToken",
    "Currency",
    "PaymentMethod",
    "TransactionType",
    "TransactionStatusModel",
    "RiskLevelCode",
    "Merchant",
    "Agent",
    "Device",
    "Location",
    "Transaction",
    "FraudAlert",
    "FraudCase",
    "FraudRule",
    "Prediction",
    "PredictionExplanation",
    "RiskAssessment",
    "InvestigationTimeline",
    "FraudComment",
    "FraudAttachment",
]
