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


class TransactionStatusValue(str, Enum):
    """Transaction statuses matching architecture doc."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FLAGGED = "flagged"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    REVERSED = "reversed"


class RiskLevelValue(str, Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionChannel(str, Enum):
    """Transaction origination channels."""
    MOBILE_APP = "mobile_app"
    WEB = "web"
    USSD = "ussd"
    API = "api"
    POS = "pos"
    ATM = "atm"
    AGENT = "agent"
    BRANCH = "branch"


class SourceSystem(str, Enum):
    """External system originating the transaction."""
    CORE_BANKING = "core_banking"
    SWITCH = "switch"
    WALLET = "wallet"
    PAYMENT_GATEWAY = "payment_gateway"
    BILL_PAY = "bill_pay"
    THIRD_PARTY = "third_party"
    MANUAL = "manual"
