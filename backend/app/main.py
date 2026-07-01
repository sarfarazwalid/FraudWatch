"""
FraudWatch API Application Factory

This module creates and configures the FastAPI application instance.
Follows the application factory pattern for better testability and configuration.
"""

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
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
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

    # Include API routers here (will be added as features are implemented)
    # from app.api.v1.auth import router as auth_router
    # application.include_router(auth_router, prefix=settings.api_v1_prefix)

    return application


# Create the application instance
app = create_application()