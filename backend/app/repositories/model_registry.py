"""
ModelRegistry Repository Implementation.

Data access layer for ModelRegistry model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.ml.model_registry import ModelRegistry
from app.models.ml.enums import DeploymentEnvironment
from app.repositories.base import BaseRepository


class ModelRegistryRepository(BaseRepository[ModelRegistry, Any, Any]):
    """
    Repository for ModelRegistry model.

    Provides model registry-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(ModelRegistry, session)

    async def get_by_model_name(self, model_name: str) -> Optional[ModelRegistry]:
        """Get model registry entry by model name."""
        return await self.get_by_field("model_name", model_name)

    async def get_active_models(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelRegistry]:
        """Get all active model registry entries."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"active": True}
        )

    async def get_by_environment(
        self,
        environment: DeploymentEnvironment,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelRegistry]:
        """Get models by deployment environment."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"deployment_environment": environment}
        )

    async def get_production_models(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelRegistry]:
        """Get all production models."""
        return await self.get_by_environment(DeploymentEnvironment.PRODUCTION, skip, limit)
