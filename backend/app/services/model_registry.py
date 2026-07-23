"""
ModelRegistry service.

Handles ML model registry business logic.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from app.models.ml.model_registry import ModelRegistry
from app.models.ml.enums import DeploymentEnvironment, ModelStatus
from app.repositories.model_registry import ModelRegistryRepository
from sqlalchemy import select, or_, and_


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

    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[ModelRegistry], int]:
        """
        Get paginated, filtered, and sorted models.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for model name
            filters: Dictionary of field filters (model_type, status, is_active)
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (items, total_count)
        """
        # Build base query
        query = select(ModelRegistry)
        count_query = select(ModelRegistry.id)

        # Apply search filter
        conditions = []
        if search:
            conditions.append(or_(
                ModelRegistry.model_name.ilike(f"%{search}%"),
            ))

        # Apply filters
        if filters:
            if "model_type" in filters and filters["model_type"]:
                conditions.append(ModelRegistry.algorithm == filters["model_type"])
            if "status" in filters and filters["status"]:
                conditions.append(ModelRegistry.status == filters["status"])
            if "is_active" in filters and filters["is_active"] is not None:
                conditions.append(ModelRegistry.is_active == filters["is_active"])

        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.model_registry_repo.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Apply sorting
        sort_field = getattr(ModelRegistry, sort_by, ModelRegistry.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.model_registry_repo.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create_model(self, model_data: dict, created_by: str) -> ModelRegistry:
        """
        Register a new model in the registry.

        Args:
            model_data: Model registration data
            created_by: User ID who created the model

        Returns:
            Created registry entry
        """
        model_data["created_by_id"] = created_by
        registry_entry = ModelRegistry(**model_data)
        self.model_registry_repo.session.add(registry_entry)
        await self.model_registry_repo.session.flush()
        await self.model_registry_repo.session.refresh(registry_entry)
        return registry_entry

    async def deploy_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Deploy a model to production."""
        registry_entry = await self.model_registry_repo.get(model_id)
        if not registry_entry:
            return None

        registry_entry.status = ModelStatus.PRODUCTION
        registry_entry.deployed = True
        registry_entry.deployment_date = datetime.now()

        await self.model_registry_repo.session.flush()
        await self.model_registry_repo.session.refresh(registry_entry)
        return registry_entry

    async def archive_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Archive a model."""
        registry_entry = await self.model_registry_repo.get(model_id)
        if not registry_entry:
            return None

        registry_entry.status = ModelStatus.ARCHIVED
        registry_entry.is_active = False

        await self.model_registry_repo.session.flush()
        await self.model_registry_repo.session.refresh(registry_entry)
        return registry_entry
