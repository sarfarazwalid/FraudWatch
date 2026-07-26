from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction.transaction import Transaction
from app.models.transaction.device import Device
from app.models.transaction.location import Location
from app.models.transaction.merchant import Merchant
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.schemas.fraud import (
    FraudAnalysisRequest,
    FraudAnalysisResponse,
    PredictionResponse,
    RuleEvaluationResponse,
    RuleEvaluationResult,
    AlertResponse,
    CaseResponse,
)
from app.services.prediction import PredictionService
from app.services.fraud_rule import FraudRuleService
from app.services.fraud_alert import FraudAlertService
from app.services.fraud_case import FraudCaseService

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

    async def create_transaction_with_fraud_check(
        self,
        request: FraudAnalysisRequest,
        current_user,
    ) -> FraudAnalysisResponse:
        """
        Create a transaction and immediately perform fraud analysis.

        Workflow:
        1. Create transaction record
        2. Extract fraud features (amount, velocity, device, location, merchant)
        3. Run rule engine evaluation
        4. Run ML prediction (with fallback scoring)
        5. Create alert if risk_score >= 0.7
        6. Create case if risk_score >= 0.85

        Args:
            request: Transaction analysis request data
            current_user: Authenticated user

        Returns:
            FraudAnalysisResponse with transaction, prediction, rules, alert, case
        """
        session = self.transaction_repo.session

        # 1. Create transaction
        transaction = await self._create_transaction_from_request(request, current_user)

        # 2. Extract fraud features
        features = await self._extract_fraud_features(transaction, request)

        # 3. Run rule engine evaluation
        rule_service = FraudRuleService.__new__(FraudRuleService)
        rule_service.session = session
        rule_evaluations = await rule_service.evaluate_transaction(transaction, features)

        # 4. Run ML prediction
        prediction_service = PredictionService(session)
        prediction = await prediction_service.predict_transaction_risk(transaction, features)

        # 5. Create alert if risk_score >= 0.7
        alert = None
        if prediction.risk_score >= 0.7:
            alert_service = FraudAlertService.__new__(FraudAlertService)
            alert_service.session = session
            alert = await alert_service.create_from_prediction(
                transaction=transaction,
                prediction=prediction,
                rule_evaluations=rule_evaluations,
                current_user=current_user,
            )

        # 6. Create case if risk_score >= 0.85
        case = None
        if prediction.risk_score >= 0.85 and alert:
            case_service = FraudCaseService.__new__(FraudCaseService)
            case_service.session = session
            case = await case_service.create_from_alert(
                alert=alert,
                prediction=prediction,
                rule_evaluations=rule_evaluations,
                current_user=current_user,
            )

        await session.flush()

        return FraudAnalysisResponse(
            transaction={
                "id": str(transaction.id),
                "transaction_reference": transaction.transaction_reference,
                "amount": float(transaction.amount),
                "channel": transaction.channel.value if transaction.channel else None,
                "sender_identifier": transaction.sender_identifier,
                "receiver_identifier": transaction.receiver_identifier,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
            },
            prediction=prediction,
            rule_evaluations=rule_evaluations,
            alert=alert,
            case=case,
        )

    async def _create_transaction_from_request(
        self,
        request: FraudAnalysisRequest,
        current_user,
    ) -> Transaction:
        """Create a Transaction model from a FraudAnalysisRequest."""
        from app.models.transaction.transaction_type import TransactionType
        from app.models.transaction.currency import Currency
        from app.models.transaction.payment_method import PaymentMethod
        from app.models.transaction.transaction_status import TransactionStatusModel
        from app.models.enums import TransactionStatusValue

        # Get or create reference transaction type
        tx_type_result = await self.transaction_repo.session.execute(
            __import__("sqlalchemy").select(TransactionType).limit(1)
        )
        tx_type = tx_type_result.scalar_one_or_none()

        # Get or create reference currency
        currency_result = await self.transaction_repo.session.execute(
            __import__("sqlalchemy").select(Currency).limit(1)
        )
        currency = currency_result.scalar_one_or_none()

        # Get or create reference payment method
        pm_result = await self.transaction_repo.session.execute(
            __import__("sqlalchemy").select(PaymentMethod).limit(1)
        )
        payment_method = pm_result.scalar_one_or_none()

        # Get completed status
        status_result = await self.transaction_repo.session.execute(
            __import__("sqlalchemy").select(TransactionStatusModel).where(
                TransactionStatusModel.code == TransactionStatusValue.COMPLETED.value
            ).limit(1)
        )
        status = status_result.scalar_one_or_none()

        import uuid
        transaction = Transaction(
            transaction_reference=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            external_reference=request.transaction_metadata.get("external_reference") if request.transaction_metadata else None,
            sender_identifier=request.sender_identifier or f"sender_{uuid.uuid4().hex[:8]}",
            receiver_identifier=request.receiver_identifier or f"receiver_{uuid.uuid4().hex[:8]}",
            merchant_id=request.merchant_id,
            device_id=request.device_id,
            location_id=request.location_id,
            currency_id=currency.id if currency else None,
            payment_method_id=payment_method.id if payment_method else None,
            transaction_type_id=tx_type.id if tx_type else None,
            status_id=status.id if status else None,
            amount=request.amount,
            fee=0.0,
            net_amount=request.amount,
            transaction_timestamp=datetime.now(timezone.utc),
            channel=request.channel,
            description=f"Fraud analysis transaction - {request.amount} {request.currency}",
            transaction_metadata=request.transaction_metadata,
        )
        self.transaction_repo.session.add(transaction)
        await self.transaction_repo.session.flush()
        await self.transaction_repo.session.refresh(transaction)
        return transaction

    async def _extract_fraud_features(
        self,
        transaction: Transaction,
        request: FraudAnalysisRequest,
    ) -> Dict[str, Any]:
        """
        Extract fraud detection features from transaction and related data.

        Returns feature dictionary with:
        - amount_score: Based on amount vs user average
        - velocity_score: Based on recent transaction frequency
        - device_score: Based on device trust score
        - location_score: Based on country risk and VPN status
        - merchant_score: Based on merchant risk tier
        - user_average_amount: User's historical average
        - recent_transaction_count: Recent transaction count
        - vpn_detected: Whether VPN/proxy detected
        - country_risk_high: Whether country is high risk
        """
        features: Dict[str, Any] = {}

        # --- Amount Features ---
        amount = float(transaction.amount)
        # Amount score: higher amounts = higher risk (sigmoid-like scaling)
        if amount <= 100:
            amount_score = 0.0
        elif amount <= 500:
            amount_score = 0.2
        elif amount <= 1000:
            amount_score = 0.4
        elif amount <= 5000:
            amount_score = 0.6
        elif amount <= 10000:
            amount_score = 0.8
        else:
            amount_score = 1.0
        features["amount_score"] = amount_score
        features["amount"] = amount

        # Get user average amount for rule engine
        prediction_service = PredictionService(self.transaction_repo.session)
        if transaction.sender_identifier:
            user_avg = await prediction_service.get_user_average_amount(
                transaction.sender_identifier
            )
            features["user_average_amount"] = user_avg
        else:
            features["user_average_amount"] = 0.0

        # --- Velocity Features ---
        velocity_count = 0
        velocity_score = 0.0
        if transaction.sender_identifier:
            velocity_count, velocity_score = (
                await prediction_service.get_transaction_velocity_features(
                    transaction.sender_identifier, minutes=5
                )
            )
        features["velocity_score"] = velocity_score
        features["recent_transaction_count"] = velocity_count

        # --- Device Features ---
        device_score = 0.0
        if transaction.device_id:
            device_result = await self.transaction_repo.session.execute(
                __import__("sqlalchemy").select(Device).where(
                    Device.id == transaction.device_id
                ).limit(1)
            )
            device = device_result.scalar_one_or_none()
            if device:
                # Trusted devices have lower risk
                if device.trusted:
                    device_score = 0.1
                else:
                    device_score = 0.5
                # New devices (first seen recently) have higher risk
                if device.last_seen and (
                    datetime.now(timezone.utc) - device.last_seen
                ) < timedelta(hours=24):
                    device_score = min(device_score + 0.3, 1.0)
            else:
                device_score = 0.7  # Unknown device = high risk
        else:
            device_score = 0.5  # No device info = medium risk
        features["device_score"] = device_score

        # --- Location Features ---
        location_score = 0.0
        vpn_detected = False
        country_risk_high = False
        if transaction.location_id:
            location_result = await self.transaction_repo.session.execute(
                __import__("sqlalchemy").select(Location).where(
                    Location.id == transaction.location_id
                ).limit(1)
            )
            location = location_result.scalar_one_or_none()
            if location:
                # High-risk countries (simplified)
                high_risk_countries = {"NG", "RU", "CN", "IR", "KP", "SY", "VE", "MM", "AF", "IQ"}
                if location.country and location.country.upper() in high_risk_countries:
                    location_score = 0.8
                    country_risk_high = True
                else:
                    location_score = 0.2
        features["location_score"] = location_score
        features["vpn_detected"] = vpn_detected
        features["country_risk_high"] = country_risk_high

        # --- Merchant Features ---
        merchant_score = 0.0
        if transaction.merchant_id:
            merchant_result = await self.transaction_repo.session.execute(
                __import__("sqlalchemy").select(Merchant).where(
                    Merchant.id == transaction.merchant_id
                ).limit(1)
            )
            merchant = merchant_result.scalar_one_or_none()
            if merchant:
                # Map merchant risk rating to score
                risk_map = {
                    "low": 0.1,
                    "medium": 0.4,
                    "high": 0.7,
                    "critical": 1.0,
                }
                merchant_score = risk_map.get(
                    merchant.risk_rating.lower() if merchant.risk_rating else "", 0.3
                )
        features["merchant_score"] = merchant_score

        return features

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
