"""
Database connection management.

This module provides async and sync database engines and session factories.
Configured for PostgreSQL with SQLAlchemy 2.x async support.
"""

from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings


# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# Async engine for FastAPI endpoints
async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    poolclass=QueuePool,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic migrations and Celery tasks
sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.database_echo,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    poolclass=QueuePool,
)

# Sync session factory
SessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session for async operations
    
    Usage:
        @router.get("/items/")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Generator:
    """
    Dependency for getting sync database sessions.
    
    Yields:
        Session: Database session for sync operations
    
    Usage:
        def some_sync_task():
            with get_sync_session() as session:
                ...
    """
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()