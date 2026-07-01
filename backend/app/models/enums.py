"""
SQLAlchemy Enums for FraudWatch.

Defines all enumerated types used across the application.
Uses Python Enums mapped to PostgreSQL ENUM types.
"""

from enum import Enum


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


class RoleType(str, Enum):
    """System role types."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    FRAUD_ANALYST = "fraud_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    VIEWER = "viewer"


class PermissionAction(str, Enum):
    """CRUD + Execute actions for permissions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class SessionStatus(str, Enum):
    """User session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TokenType(str, Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"


class AuthenticationProvider(str, Enum):
    """Authentication provider types."""
    LOCAL = "local"
    SSO = "sso"
    OAUTH2 = "oauth2"