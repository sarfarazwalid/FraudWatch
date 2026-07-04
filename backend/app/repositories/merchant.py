"""
Merchant Repository Implementation.

Data access layer for Merchant model with specific query methods.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Optional

from app.models.transaction.merchant import Merchant
from app.repositories.base import BaseRepository


class MerchantRepository(BaseRepository[Merchant, Any, Any]):
    """
    Repository for Merchant model.

    Provides merchant-specific query methods beyond generic CRUD.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Merchant, session)

    async def get_by_merchant_code(self, merchant_code: str) -> Optional[Merchant]:
        """Get merchant by merchant code."""
        return await self.get_by_field("merchant_code", merchant_code)

    async def get_active_merchants(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Merchant]:
        """Get all active merchants."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True, "deleted_at": None}
        )

    async def search_merchants(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Merchant]:
        """Search merchants by name or code."""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Merchant).where(
                (Merchant.name.ilike(search_pattern)) |
                (Merchant.merchant_code.ilike(search_pattern))
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
