"""
FraudWatch API Application Factory

This module creates and configures the FastAPI application instance.
Follows the application factory pattern for better testability and configuration.
"""

import sys
from pathlib import Path

# Add parent directory to path to import ml module BEFORE other imports
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.core.logging import setup_logging

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# Import all models FIRST to ensure they're registered with SQLAlchemy
# before any database connections are established
from app.models import (
    User,
    Role,
    Permission,
    RolePermission,
    UserSession,
    RefreshToken,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup:
        - Initialize database connections
        - Load ML models
        - Start background workers

    Shutdown:
        - Close database connections
        - Cleanup resources
    """
    logger.info(f"Starting {settings.project_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")

    # Startup logic here (database initialization, model loading, etc.)
    yield

    # Shutdown logic here
    logger.info(f"Shutting down {settings.project_name}")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    application = FastAPI(
        title=settings.project_name,
        description=settings.description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Global exception handlers
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        # Always return detailed error for debugging
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__,
            },
        )

    # Health check endpoint
    @application.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.version,
            "environment": settings.environment,
        }

    # Version endpoint
    @application.get(f"{settings.api_v1_prefix}/version", tags=["Health"])
    async def version():
        return {
            "name": settings.project_name,
            "version": settings.version,
        }

    # Include API routers
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

    api_prefix = settings.api_v1_prefix

    application.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
    application.include_router(users_router, prefix=f"{api_prefix}/users", tags=["Users"])
    application.include_router(roles_router, prefix=f"{api_prefix}/roles", tags=["Roles"])
    application.include_router(permissions_router, prefix=f"{api_prefix}/permissions", tags=["Permissions"])
    application.include_router(transactions_router, prefix=f"{api_prefix}", tags=["Transactions"])
    application.include_router(merchants_router, prefix=f"{api_prefix}/merchants", tags=["Merchants"])
    application.include_router(devices_router, prefix=f"{api_prefix}/devices", tags=["Devices"])
    application.include_router(locations_router, prefix=f"{api_prefix}/locations", tags=["Locations"])
    application.include_router(fraud_alerts_router, prefix=f"{api_prefix}/fraud/alerts", tags=["Fraud Alerts"])
    application.include_router(fraud_cases_router, prefix=f"{api_prefix}/fraud/cases", tags=["Fraud Cases"])
    application.include_router(fraud_rules_router, prefix=f"{api_prefix}/fraud/rules", tags=["Fraud Rules"])
    application.include_router(model_registry_router, prefix=f"{api_prefix}/ml/models", tags=["Model Registry"])

    return application


# Create the application instance
app = create_application()
