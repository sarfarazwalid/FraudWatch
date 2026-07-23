from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from app.models.transaction.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate

class TransactionService:
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo

    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        # Create transaction from schema
        transaction = Transaction(
            transaction_reference=transaction_data.transaction_reference,
            external_reference=transaction_data.external_reference,
            sender_identifier=transaction_data.sender_identifier,
            receiver_identifier=transaction_data.receiver_identifier,
            merchant_id=transaction_data.merchant_id,
            agent_id=transaction_data.agent_id,
            device_id=transaction_data.device_id,
            location_id=transaction_data.location_id,
            currency_id=transaction_data.currency_id,
            payment_method_id=transaction_data.payment_method_id,
            transaction_type_id=transaction_data.transaction_type_id,
            status_id=transaction_data.status_id,
            risk_level_id=transaction_data.risk_level_id,
            amount=transaction_data.amount,
            fee=transaction_data.fee,
            net_amount=transaction_data.net_amount,
            exchange_rate=transaction_data.exchange_rate,
            transaction_timestamp=transaction_data.transaction_timestamp,
            channel=transaction_data.channel,
            source_system=transaction_data.source_system,
            description=transaction_data.description,
            transaction_metadata=transaction_data.transaction_metadata,
        )

        self.transaction_repo.session.add(transaction)
        await self.transaction_repo.session.flush()
        await self.transaction_repo.session.refresh(transaction)

        # Publish event to Celery for async fraud prediction
        # Lazy import to avoid circular dependency:
        # prediction_tasks -> PredictionService -> services.__init__ -> TransactionService -> prediction_tasks
        try:
            from app.workers.tasks.prediction_tasks import predict_transaction_task
            predict_transaction_task.delay(
                transaction_id=transaction.id,
                correlation_id=str(transaction.id),
            )
        except Exception as e:
            # Log error but don't fail transaction creation
            # In production: structured logging
            print(f"Failed to queue prediction task: {e}")

        return transaction

    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return await self.transaction_repo.get(transaction_id)

    async def get_transaction_by_reference(self, reference: str) -> Optional[Transaction]:
        # Placeholder for transaction reference lookup
        return None

    async def update_transaction(
        self,
        transaction_id: str,
        update_data: TransactionUpdate
    ) -> Optional[Transaction]:

        transaction = await self.transaction_repo.get(transaction_id)
        if not transaction:
            return None

        # Only allow updating specific fields
        allowed_fields = ["status_id", "risk_level_id", "description"]
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if field in allowed_fields:
                setattr(transaction, field, value)

        transaction.updated_at = datetime.now(timezone.utc)

        await self.transaction_repo.session.flush()
        await self.transaction_repo.session.refresh(transaction)

        return transaction

    async def delete_transaction(self, transaction_id: str) -> bool:
        transaction = await self.transaction_repo.get(transaction_id)
        if not transaction:
            return False

        # Soft delete
        transaction.deleted_at = datetime.now(timezone.utc)
        await self.transaction_repo.session.flush()

        return True

    async def get_transactions(
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
    ) -> Tuple[List[Transaction], int]:
        """
        Get paginated, filtered, and sorted transactions.

        Returns:
            Tuple of (items, total_count)
        """
        return await self.transaction_repo.list_transactions(
            page=page,
            page_size=page_size,
            search=search,
            merchant_id=merchant_id,
            status_id=status_id,
            risk_level_id=risk_level_id,
            payment_method_id=payment_method_id,
            transaction_type_id=transaction_type_id,
            device_id=device_id,
            location_id=location_id,
            amount_min=amount_min,
            amount_max=amount_max,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

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
    ) -> Tuple[List[Transaction], int]:
        """
        Alias for get_transactions to maintain backward compatibility.
        """
        return await self.get_transactions(
            page=page,
            page_size=page_size,
            search=search,
            merchant_id=merchant_id,
            status_id=status_id,
            risk_level_id=risk_level_id,
            payment_method_id=payment_method_id,
            transaction_type_id=transaction_type_id,
            device_id=device_id,
            location_id=location_id,
            amount_min=amount_min,
            amount_max=amount_max,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
