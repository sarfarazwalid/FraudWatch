"""
Service dependencies for FastAPI dependency injection.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.repositories.permission import PermissionRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.session import SessionRepository
from app.services.user import UserService
from app.services.role import RoleService
from app.services.permission import PermissionService
from app.services.auth import AuthenticationService
from app.services.session import SessionService
from app.services.refresh_token import RefreshTokenService


# Database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# Repository dependencies
async def get_user_repo(db_session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Get user repository."""
    return UserRepository(db_session)


async def get_role_repo(db_session: AsyncSession = Depends(get_db_session)) -> RoleRepository:
    """Get role repository."""
    return RoleRepository(db_session)


async def get_permission_repo(db_session: AsyncSession = Depends(get_db_session)) -> PermissionRepository:
    """Get permission repository."""
    return PermissionRepository(db_session)


async def get_refresh_token_repo(db_session: AsyncSession = Depends(get_db_session)) -> RefreshTokenRepository:
    """Get refresh token repository."""
    return RefreshTokenRepository(db_session)


async def get_session_repo(db_session: AsyncSession = Depends(get_db_session)) -> SessionRepository:
    """Get session repository."""
    return SessionRepository(db_session)


# Service dependencies
async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo)
) -> UserService:
    """Get user service."""
    return UserService(user_repo, role_repo)


async def get_role_service(
    role_repo: RoleRepository = Depends(get_role_repo),
    permission_repo: PermissionRepository = Depends(get_permission_repo)
) -> RoleService:
    """Get role service."""
    return RoleService(role_repo, permission_repo)


async def get_permission_service(
    permission_repo: PermissionRepository = Depends(get_permission_repo)
) -> PermissionService:
    """Get permission service."""
    return PermissionService(permission_repo)


async def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repo),
    user_repo: UserRepository = Depends(get_user_repo)
) -> SessionService:
    """Get session service."""
    return SessionService(session_repo, user_repo)


async def get_refresh_token_service(
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repo),
    user_repo: UserRepository = Depends(get_user_repo)
) -> RefreshTokenService:
    """Get refresh token service."""
    return RefreshTokenService(refresh_token_repo, user_repo)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    session_service: SessionService = Depends(get_session_service)
) -> AuthenticationService:
    """Get authentication service."""
    return AuthenticationService(user_repo, role_repo, refresh_token_service, session_service)