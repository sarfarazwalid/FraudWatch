"""
Merchant service.

Handles merchant management business logic.
"""

from typing import Optional, List

from app.models.transaction.merchant import Merchant
from app.repositories.merchant import MerchantRepository


class MerchantService:
    """
    Service for merchant operations.

    Handles merchant creation, updates, and retrieval.
    """

    def __init__(self, merchant_repo: MerchantRepository):
        self.merchant_repo = merchant_repo

    async def create_merchant(self, merchant_data: dict) -> Merchant:
        """
        Create a new merchant.

        Args:
            merchant_data: Merchant creation data

        Returns:
            Created merchant
        """
        merchant = Merchant(**merchant_data)
        self.merchant_repo.session.add(merchant)
        await self.merchant_repo.session.flush()
        await self.merchant_repo.session.refresh(merchant)
        return merchant

    async def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        """Get merchant by ID."""
        return await self.merchant_repo.get(merchant_id)

    async def get_merchant_by_code(self, merchant_code: str) -> Optional[Merchant]:
        """Get merchant by merchant code."""
        return await self.merchant_repo.get_by_merchant_code(merchant_code)

    async def update_merchant(self, merchant_id: str, update_data: dict) -> Optional[Merchant]:
        """Update merchant."""
        merchant = await self.merchant_repo.get(merchant_id)
        if not merchant:
            return None

        for field, value in update_data.items():
            if hasattr(merchant, field) and value is not None:
                setattr(merchant, field, value)

        await self.merchant_repo.session.flush()
        await self.merchant_repo.session.refresh(merchant)
        return merchant

    async def get_active_merchants(self, skip: int = 0, limit: int = 100) -> List[Merchant]:
        """Get all active merchants."""
        return await self.merchant_repo.get_active_merchants(skip, limit)

    async def search_merchants(self, query: str, skip: int = 0, limit: int = 100) -> List[Merchant]:
        """Search merchants."""
        return await self.merchant_repo.search_merchants(query, skip, limit)
