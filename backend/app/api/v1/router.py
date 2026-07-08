from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.roles import router as roles_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.devices import router as devices_router
from app.api.v1.locations import router as locations_router
from app.api.v1.fraud_alerts import router as fraud_alerts_router
from app.api.v1.fraud_cases import router as fraud_cases_router
from app.api.v1.fraud_rules import router as fraud_rules_router
from app.api.v1.model_registry import router as model_registry_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(roles_router, prefix="/roles", tags=["Roles"])
router.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
router.include_router(merchants_router, prefix="/merchants", tags=["Merchants"])
router.include_router(devices_router, prefix="/devices", tags=["Devices"])
router.include_router(locations_router, prefix="/locations", tags=["Locations"])
router.include_router(fraud_alerts_router, prefix="/fraud/alerts", tags=["Fraud Alerts"])
router.include_router(fraud_cases_router, prefix="/fraud/cases", tags=["Fraud Cases"])
router.include_router(fraud_rules_router, prefix="/fraud/rules", tags=["Fraud Rules"])
router.include_router(model_registry_router, prefix="/ml/models", tags=["Model Registry"])
