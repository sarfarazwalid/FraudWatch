"""
Application settings and configuration management.

This module loads configuration from environment variables using Pydantic Settings.
All settings are validated at startup to ensure required values are present.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"

    # Database
    database_url: str = "postgresql+asyncpg://fraudwatch:fraudwatch_password@localhost:5432/fraudwatch_db"
    database_sync_url: str = "postgresql://fraudwatch:fraudwatch_password@localhost:5432/fraudwatch_db"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-base64-32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Password Hashing
    password_secret_key: str = "change-me-in-production"
    password_algorithm: str = "bcrypt"
    password_rounds: int = 12

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "FraudWatch API"
    version: str = "1.0.0"
    description: str = "AI-Powered Financial Fraud Detection & Risk Intelligence Platform"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Sentry
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1

    # ML
    model_path: str = "./ml/artifacts"
    model_version: str = "latest"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


# Global settings instance
settings = Settings()