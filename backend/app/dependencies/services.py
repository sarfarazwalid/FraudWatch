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
from app.repositories.transaction import TransactionRepository
from app.repositories.merchant import MerchantRepository
from app.repositories.device import DeviceRepository
from app.repositories.location import LocationRepository
from app.repositories.fraud_alert import FraudAlertRepository
from app.repositories.fraud_case import FraudCaseRepository
from app.repositories.fraud_rule import FraudRuleRepository
from app.repositories.investigation_timeline import InvestigationTimelineRepository
from app.repositories.model_registry import ModelRegistryRepository
from app.services.user import UserService
from app.services.role import RoleService
from app.services.permission import PermissionService
from app.services.auth import AuthenticationService
from app.services.session import SessionService
from app.services.refresh_token import RefreshTokenService
from app.services.transaction import TransactionService
from app.services.merchant import MerchantService
from app.services.device import DeviceService
from app.services.location import LocationService
from app.services.fraud_alert import FraudAlertService
from app.services.fraud_case import FraudCaseService
from app.services.fraud_rule import FraudRuleService
from app.services.investigation_timeline import InvestigationTimelineService
from app.services.model_registry import ModelRegistryService


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


async def get_transaction_repo(db_session: AsyncSession = Depends(get_db_session)) -> TransactionRepository:
    """Get transaction repository."""
    return TransactionRepository(db_session)


async def get_merchant_repo(db_session: AsyncSession = Depends(get_db_session)) -> MerchantRepository:
    """Get merchant repository."""
    return MerchantRepository(db_session)


async def get_device_repo(db_session: AsyncSession = Depends(get_db_session)) -> DeviceRepository:
    """Get device repository."""
    return DeviceRepository(db_session)


async def get_location_repo(db_session: AsyncSession = Depends(get_db_session)) -> LocationRepository:
    """Get location repository."""
    return LocationRepository(db_session)


async def get_fraud_alert_repo(db_session: AsyncSession = Depends(get_db_session)) -> FraudAlertRepository:
    """Get fraud alert repository."""
    return FraudAlertRepository(db_session)


async def get_fraud_case_repo(db_session: AsyncSession = Depends(get_db_session)) -> FraudCaseRepository:
    """Get fraud case repository."""
    return FraudCaseRepository(db_session)


async def get_fraud_rule_repo(db_session: AsyncSession = Depends(get_db_session)) -> FraudRuleRepository:
    """Get fraud rule repository."""
    return FraudRuleRepository(db_session)


async def get_investigation_timeline_repo(db_session: AsyncSession = Depends(get_db_session)) -> InvestigationTimelineRepository:
    """Get investigation timeline repository."""
    return InvestigationTimelineRepository(db_session)


async def get_model_registry_repo(db_session: AsyncSession = Depends(get_db_session)) -> ModelRegistryRepository:
    """Get model registry repository."""
    return ModelRegistryRepository(db_session)


# Service dependencies
async def get_transaction_service(
    transaction_repo: TransactionRepository = Depends(get_transaction_repo)
) -> TransactionService:
    """Get transaction service."""
    return TransactionService(transaction_repo)


async def get_merchant_service(
    merchant_repo: MerchantRepository = Depends(get_merchant_repo)
) -> MerchantService:
    """Get merchant service."""
    return MerchantService(merchant_repo)


async def get_device_service(
    device_repo: DeviceRepository = Depends(get_device_repo)
) -> DeviceService:
    """Get device service."""
    return DeviceService(device_repo)


async def get_location_service(
    location_repo: LocationRepository = Depends(get_location_repo)
) -> LocationService:
    """Get location service."""
    return LocationService(location_repo)


async def get_fraud_alert_service(
    fraud_alert_repo: FraudAlertRepository = Depends(get_fraud_alert_repo)
) -> FraudAlertService:
    """Get fraud alert service."""
    return FraudAlertService(fraud_alert_repo)


async def get_fraud_case_service(
    fraud_case_repo: FraudCaseRepository = Depends(get_fraud_case_repo)
) -> FraudCaseService:
    """Get fraud case service."""
    return FraudCaseService(fraud_case_repo)


async def get_fraud_rule_service(
    fraud_rule_repo: FraudRuleRepository = Depends(get_fraud_rule_repo)
) -> FraudRuleService:
    """Get fraud rule service."""
    return FraudRuleService(fraud_rule_repo)


async def get_investigation_timeline_service(
    investigation_timeline_repo: InvestigationTimelineRepository = Depends(get_investigation_timeline_repo)
) -> InvestigationTimelineService:
    """Get investigation timeline service."""
    return InvestigationTimelineService(investigation_timeline_repo)


async def get_model_registry_service(
    model_registry_repo: ModelRegistryRepository = Depends(get_model_registry_repo)
) -> ModelRegistryService:
    """Get model registry service."""
    return ModelRegistryService(model_registry_repo)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    role_repo: RoleRepository = Depends(get_role_repo),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    session_service: SessionService = Depends(get_session_service)
) -> AuthenticationService:
    """Get authentication service."""
    return AuthenticationService(user_repo, role_repo, refresh_token_service, session_service)
