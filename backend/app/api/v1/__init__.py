"""
API v1 routes.
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.roles import router as roles_router

router = APIRouter()

# Include sub-routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(roles_router, prefix="/roles", tags=["Roles"])