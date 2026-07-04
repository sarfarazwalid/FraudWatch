"""
ModelRegistry service.

Handles ML model registry business logic.
"""

from typing import Optional, List

from app.models.ml.model_registry import ModelRegistry
from app.models.ml.enums import DeploymentEnvironment
from app.repositories.model_registry import ModelRegistryRepository


class ModelRegistryService:
    """
    Service for model registry operations.

    Handles model registration, deployment, and rollback.
    """

    def __init__(self, model_registry_repo: ModelRegistryRepository):
        self.model_registry_repo = model_registry_repo

    async def register_model(self, model_data: dict) -> ModelRegistry:
        """
        Register a new model in the registry.

        Args:
            model_data: Model registration data

        Returns:
            Created registry entry
        """
        registry_entry = ModelRegistry(**model_data)
        self.model_registry_repo.session.add(registry_entry)
        await self.model_registry_repo.session.flush()
        await self.model_registry_repo.session.refresh(registry_entry)
        return registry_entry

    async def get_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Get model registry entry by ID."""
        return await self.model_registry_repo.get(model_id)

    async def get_model_by_name(self, model_name: str) -> Optional[ModelRegistry]:
        """Get model registry entry by model name."""
        return await self.model_registry_repo.get_by_model_name(model_name)

    async def update_model(
        self,
        model_id: str,
        update_data: dict
    ) -> Optional[ModelRegistry]:
        """Update model registry entry."""
        registry_entry = await self.model_registry_repo.get(model_id)
        if not registry_entry:
            return None

        for field, value in update_data.items():
            if hasattr(registry_entry, field) and value is not None:
                setattr(registry_entry, field, value)

        await self.model_registry_repo.session.flush()
        await self.model_registry_repo.session.refresh(registry_entry)
        return registry_entry

    async def get_production_models(self, skip: int = 0, limit: int = 100) -> List[ModelRegistry]:
        """Get all production models."""
        return await self.model_registry_repo.get_production_models(skip, limit)
