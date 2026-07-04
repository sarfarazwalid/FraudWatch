"""
Base seeder class for all seeders.

Provides common functionality for database seeding operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class BaseSeeder(ABC):
    """Abstract base class for all seeders."""

    def __init__(self, session: AsyncSession, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self.stats: dict[str, int] = {}

    @abstractmethod
    async def seed(self) -> dict[str, int]:
        """Execute the seeding logic. Returns stats dict."""
        pass

    async def clear_table(self, table_name: str) -> None:
        """Clear all rows from a table."""
        await self.session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        await self.session.flush()

    async def bulk_insert(self, model_class: Any, records: list[dict]) -> list[Any]:
        """
        Bulk insert records using SQLAlchemy.
        Returns the inserted objects.
        """
        if not records:
            return []

        self.session.add_all([model_class(**r) for r in records])
        await self.session.flush()
        return records

    async def bulk_insert_batched(self, model_class: Any, records: list[dict]) -> list[Any]:
        """
        Bulk insert records in batches to avoid memory issues.
        """
        inserted = []
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            self.session.add_all([model_class(**r) for r in batch])
            await self.session.flush()
            inserted.extend(batch)
        return inserted

    def add_stat(self, key: str, count: int = 1) -> None:
        """Add to a stat counter."""
        self.stats[key] = self.stats.get(key, 0) + count

    def get_stats(self) -> dict[str, int]:
        """Get seeding statistics."""
        return self.stats