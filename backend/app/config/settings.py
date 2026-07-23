"""
Application settings and configuration management.

This module loads configuration from environment variables using Pydantic Settings.
All settings are validated at startup to ensure required values are present.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=('settings_',),
    )

    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"

    # Database
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "fraudwatch_db"
    database_user: str = "fraudwatch"
    database_password: str = "fraudwatch_password"
    database_echo: bool = False

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Celery
    celery_broker_db: int = 1
    celery_result_backend_db: int = 2

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

    @property
    def database_url(self) -> str:
        """Construct async database URL from components."""
        return f"postgresql+asyncpg://{self.database_user}:{quote(self.database_password)}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def database_sync_url(self) -> str:
        """Construct sync database URL from components."""
        return f"postgresql://{self.database_user}:{quote(self.database_password)}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        if self.redis_password:
            return f"redis://:{quote(self.redis_password)}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker_url(self) -> str:
        """Construct Celery broker URL from components."""
        if self.redis_password:
            return f"redis://:{quote(self.redis_password)}@{self.redis_host}:{self.redis_port}/{self.celery_broker_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.celery_broker_db}"

    @property
    def celery_result_backend(self) -> str:
        """Construct Celery result backend URL from components."""
        if self.redis_password:
            return f"redis://:{quote(self.redis_password)}@{self.redis_host}:{self.redis_port}/{self.celery_result_backend_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.celery_result_backend_db}"


# Global settings instance
settings = Settings()
