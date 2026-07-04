"""
FastAPI dependencies for dependency injection.
"""

from app.dependencies.database import get_db_session
from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    require_permission,
    require_role,
)
from app.dependencies.services import (
    get_user_service,
    get_role_service,
    get_permission_service,
    get_auth_service,
    get_session_service,
    get_refresh_token_service,
)

__all__ = [
    # Database
    "get_db_session",
    # Auth
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    "require_role",
    # Services
    "get_user_service",
    "get_role_service",
    "get_permission_service",
    "get_auth_service",
    "get_session_service",
    "get_refresh_token_service",
]