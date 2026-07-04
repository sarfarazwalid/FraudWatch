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
]