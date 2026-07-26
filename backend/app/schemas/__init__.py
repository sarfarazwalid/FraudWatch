"""
Pydantic schemas for FraudWatch API.

Organized by domain for request/response validation.
"""

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    PasswordChangeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserProfileResponse,
)
from app.schemas.role import (
    RoleResponse,
    RoleCreate,
    RoleUpdate,
    PermissionResponse,
    PermissionCreate,
)
from app.schemas.session import SessionResponse
from app.schemas.fraud import (
    FraudAnalysisRequest,
    FraudAnalysisResponse,
    RuleEvaluationResult,
    RuleEvaluationResponse,
    FeatureImportance,
    PredictionResponse,
    ExplanationResponse,
    AlertResponse,
    CaseResponse,
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshRequest",
    "PasswordChangeRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    # User schemas
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "UserProfileResponse",
    # Role schemas
    "RoleResponse",
    "RoleCreate",
    "RoleUpdate",
    "PermissionResponse",
    "PermissionCreate",
    # Session schemas
    "SessionResponse",
    # Fraud schemas
    "FraudAnalysisRequest",
    "FraudAnalysisResponse",
    "RuleEvaluationResult",
    "RuleEvaluationResponse",
    "FeatureImportance",
    "PredictionResponse",
    "ExplanationResponse",
    "AlertResponse",
    "CaseResponse",
]
