"""
Custom exception classes for FraudWatch API.

Provides a hierarchy of exceptions for consistent error handling.
"""

from typing import Optional, Dict, Any


class FraudWatchException(Exception):
    """Base exception for all FraudWatch exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(FraudWatchException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class ValidationException(FraudWatchException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class AuthenticationException(FraudWatchException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
        )


class AuthorizationException(FraudWatchException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
        )


class RateLimitException(FraudWatchException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
        )


class ConflictException(FraudWatchException):
    """Raised when a conflict occurs (e.g., duplicate resource)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            details=details,
        )


class DatabaseException(FraudWatchException):
    """Raised when a database error occurs."""
    
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(
            message=message,
            status_code=500,
        )


class ExternalServiceException(FraudWatchException):
    """Raised when an external service fails."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} service error: {message}",
            status_code=503,
            details={"service": service},
        )
</parameter>
<task_progress>
- [x] Create root project structure
- [x] Initialize frontend (Next.js + TypeScript + Tailwind)
- [x] Initialize backend (FastAPI + SQLAlchemy)
- [x] Set up ML folder structure
- [x] Create Docker configuration
- [x] Configure environment variables
- [ ] Set up code quality tools
- [ ] Create documentation and Git files
- [ ] Set up CI/CD pipelines
- [x] Prepare security architecture
- [ ] Verify complete project structure
</task_progress>
</write_to_file>