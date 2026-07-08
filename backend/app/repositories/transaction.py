"""Transaction repository."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, or_, and_
from sqlalchemy.orm import selectinload
from app.models.transaction.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.repositories.base import BaseRepository

class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):  # type: ignore
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def get_with_relations(self, id: str) -> Optional[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == id).options(
                selectinload(Transaction.merchant),
                selectinload(Transaction.agent),
                selectinload(Transaction.device),
                selectinload(Transaction.location),
                selectinload(Transaction.currency),
                selectinload(Transaction.payment_method),
                selectinload(Transaction.transaction_type),
                selectinload(Transaction.status_ref),
                selectinload(Transaction.risk_level_ref),
            )
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        merchant_id: Optional[str] = None,
        status_id: Optional[str] = None,
        risk_level_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        transaction_type_id: Optional[str] = None,
        device_id: Optional[str] = None,
        location_id: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "transaction_timestamp",
        sort_order: str = "desc",
    ) -> tuple[List[Transaction], int]:
        query = select(Transaction).options(
            selectinload(Transaction.merchant),
            selectinload(Transaction.payment_method),
            selectinload(Transaction.transaction_type),
            selectinload(Transaction.status_ref),
            selectinload(Transaction.risk_level_ref),
        )
        conditions = []
        if search:
            conditions.append(or_(
                Transaction.transaction_reference.ilike(f"%{search}%"),
                Transaction.external_reference.ilike(f"%{search}%"),
                Transaction.sender_identifier.ilike(f"%{search}%"),
                Transaction.receiver_identifier.ilike(f"%{search}%"),
            ))
        if merchant_id:
            conditions.append(Transaction.merchant_id == merchant_id)
        if status_id:
            conditions.append(Transaction.status_id == status_id)
        if risk_level_id:
            conditions.append(Transaction.risk_level_id == risk_level_id)
        if payment_method_id:
            conditions.append(Transaction.payment_method_id == payment_method_id)
        if transaction_type_id:
            conditions.append(Transaction.transaction_type_id == transaction_type_id)
        if device_id:
            conditions.append(Transaction.device_id == device_id)
        if location_id:
            conditions.append(Transaction.location_id == location_id)
        if amount_min is not None:
            conditions.append(Transaction.amount >= amount_min)
        if amount_max is not None:
            conditions.append(Transaction.amount <= amount_max)
        if date_from:
            conditions.append(Transaction.transaction_timestamp >= date_from)
        if date_to:
            conditions.append(Transaction.transaction_timestamp <= date_to)
        if conditions:
            query = query.where(and_(*conditions))
        count_query = select(func.count()).select_from(Transaction)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        sort_field = getattr(Transaction, sort_by, Transaction.transaction_timestamp)
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def list(self, *args, **kwargs):  # type: ignore
        return await self.list_transactions(*args, **kwargs)

    async def get_statistics(self) -> Dict[str, Any]:
        total_result = await self.session.execute(select(func.count()).select_from(Transaction))
        total = total_result.scalar_one()
        amount_stats = await self.session.execute(
            select(func.count(), func.sum(Transaction.amount), func.avg(Transaction.amount),
                   func.median(Transaction.amount), func.max(Transaction.amount), func.min(Transaction.amount))
        )
        return {"total_transactions": total}

    async def get_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        return []
