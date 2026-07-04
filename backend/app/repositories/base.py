"""
Base Repository Pattern Implementation.

Provides generic CRUD operations for SQLAlchemy 2.x models.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic repository for database operations.
    
    Provides CRUD operations and common query patterns.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session: AsyncSession = session
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get all records with pagination, ordering, and filtering."""
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    field_attr = getattr(self.model, field)
                    query = query.where(field_attr == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                order_field = getattr(self.model, order_by[1:])
                query = query.order_by(order_field.desc())
            else:
                order_field = getattr(self.model, order_by)
                query = query.order_by(order_field.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in.model_dump())
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(self, id: Any, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update an existing record."""
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        await self.session.delete(db_obj)
        await self.session.flush()
        return True
    
    async def exists(self, id: Any) -> bool:
        """Check if a record exists."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)  # type: ignore
        )
        return result.scalar_one() > 0
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field."""
        if not hasattr(self.model, field):
            raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
        
        result = await self.session.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()
    
    async def get_many_by_field(
        self,
        field: str,
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field."""
        if not hasattr(self.model, field):
            raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
        
        field_attr = getattr(self.model, field)
        query = select(self.model).where(field_attr == value)
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
