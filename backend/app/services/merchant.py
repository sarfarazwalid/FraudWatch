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

    async def list_merchants(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[dict] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> tuple[List[Merchant], int]:
        """List merchants with pagination."""
        skip = (page - 1) * page_size
        repo_filters = {}
        if filters:
            if "status" in filters and filters["status"] is not None:
                repo_filters["status"] = filters["status"]
            if "risk_level" in filters and filters["risk_level"] is not None:
                repo_filters["risk_level"] = filters["risk_level"]
            if "country" in filters and filters["country"] is not None:
                repo_filters["country"] = filters["country"]

        if search:
            merchants = await self.merchant_repo.search_merchants(search, skip, page_size)
            total = len(merchants)
        else:
            merchants = await self.merchant_repo.get_all(
                skip=skip, limit=page_size,
                filters=repo_filters if repo_filters else None,
                order_by=sort_by if sort_order == "asc" else f"-{sort_by}",
            )
            total = await self.merchant_repo.count(filters=repo_filters if repo_filters else None)
        return merchants, total

    async def deactivate_merchant(self, merchant_id: str) -> bool:
        """Deactivate a merchant."""
        merchant = await self.merchant_repo.get(merchant_id)
        if not merchant:
            return False
        merchant.is_active = False
        await self.merchant_repo.session.flush()
        return True
