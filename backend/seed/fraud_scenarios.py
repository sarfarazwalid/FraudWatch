"""
Fraud scenario seeder for demo data.

Generates realistic normal transactions and fraud scenarios
to populate the dashboard with meaningful data.
"""

import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.transaction.transaction import Transaction
from app.models.transaction.transaction_type import TransactionType
from app.models.transaction.currency import Currency
from app.models.transaction.payment_method import PaymentMethod
from app.models.transaction.transaction_status import TransactionStatusModel
from app.models.transaction.merchant import Merchant
from app.models.transaction.device import Device
from app.models.transaction.location import Location
from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.prediction import Prediction
from app.models.fraud.prediction_explanation import PredictionExplanation
from app.models.fraud.enums import (
    AlertSeverity, AlertStatus, DetectionMethod,
    CasePriority, CaseStatus, PredictionLabel, ExplanationMethod
)
from app.models.enums import TransactionChannel, TransactionStatusValue


class FraudScenarioSeeder:
    """
    Seeds demo data with normal transactions and fraud scenarios.

    Generates:
    - 1000 normal transactions (low risk)
    - 50 high amount fraud scenarios
    - 50 velocity fraud scenarios
    - 50 location fraud scenarios
    """

    HIGH_RISK_COUNTRIES = ["NG", "RU", "CN", "IR", "KP", "SY", "VE"]

    def __init__(self, session: AsyncSession):
        self.session = session
        self._refs: Dict[str, Any] = {}

    async def _load_references(self):
        """Load reference data needed for transaction creation."""
        # Transaction type
        result = await self.session.execute(select(TransactionType).limit(1))
        self._refs["tx_type"] = result.scalar_one_or_none()

        # Currency
        result = await self.session.execute(select(Currency).limit(1))
        self._refs["currency"] = result.scalar_one_or_none()

        # Payment method
        result = await self.session.execute(select(PaymentMethod).limit(1))
        self._refs["payment_method"] = result.scalar_one_or_none()

        # Status - completed
        result = await self.session.execute(
            select(TransactionStatusModel).where(
                TransactionStatusModel.code == TransactionStatusValue.COMPLETED.value
            ).limit(1)
        )
        self._refs["status"] = result.scalar_one_or_none()

        # Merchants
        result = await self.session.execute(select(Merchant).limit(5))
        self._refs["merchants"] = list(result.scalars().all())

        # Devices
        result = await self.session.execute(select(Device).limit(5))
        self._refs["devices"] = list(result.scalars().all())

        # Locations
        result = await self.session.execute(select(Location).limit(10))
        self._refs["locations"] = list(result.scalars().all())

    def _create_transaction(
        self,
        amount: float,
        channel: str,
        sender: str,
        receiver: str,
        timestamp: datetime,
        merchant_id: Optional[str] = None,
        device_id: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> Transaction:
        """Create a transaction with the given parameters."""
        return Transaction(
            transaction_reference=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            sender_identifier=sender,
            receiver_identifier=receiver,
            merchant_id=merchant_id,
            device_id=device_id,
            location_id=location_id,
            currency_id=self._refs["currency"].id if self._refs["currency"] else None,
            payment_method_id=self._refs["payment_method"].id if self._refs["payment_method"] else None,
            transaction_type_id=self._refs["tx_type"].id if self._refs["tx_type"] else None,
            status_id=self._refs["status"].id if self._refs["status"] else None,
            amount=amount,
            fee=round(amount * 0.01, 2),
            net_amount=round(amount * 0.99, 2),
            transaction_timestamp=timestamp,
            channel=channel,
            description=f"Demo transaction - ${amount:.2f}",
        )

    def _create_prediction(
        self,
        transaction_id: str,
        risk_score: float,
        label: str,
    ) -> Prediction:
        """Create a prediction record."""
        return Prediction(
            transaction_id=transaction_id,
            model_version_id="fallback_scoring_v1",
            predicted_label=PredictionLabel(label),
            confidence_score=min(abs(risk_score - 0.5) * 2 + 0.5, 0.99),
            probability_score=risk_score,
            inference_time_ms=random.randint(5, 50),
            prediction_timestamp=datetime.now(timezone.utc),
        )

    def _create_alert(
        self,
        transaction_id: str,
        risk_score: float,
        severity: AlertSeverity,
    ) -> FraudAlert:
        """Create a fraud alert."""
        return FraudAlert(
            alert_number=f"ALR-{uuid.uuid4().hex[:8].upper()}",
            title="Suspicious transaction detected",
            description=f"Demo fraud scenario with risk score {risk_score:.2f}",
            transaction_id=transaction_id,
            severity=severity,
            status=AlertStatus.NEW,
            detection_method=DetectionMethod.HYBRID,
            risk_score=risk_score * 100,
            generated_at=datetime.now(timezone.utc),
        )

    def _create_case(self, alert_id: str, severity: str) -> FraudCase:
        """Create a fraud case linked to an alert."""
        return FraudCase(
            case_number=f"CASE-{uuid.uuid4().hex[:8].upper()}",
            alert_id=alert_id,
            severity=severity,
            priority=CasePriority.HIGH if severity in ("high", "critical") else CasePriority.MEDIUM,
            status=CaseStatus.NEW,
            escalation_level=0,
            opened_at=datetime.now(timezone.utc),
            summary=f"Auto-generated case for demo fraud scenario ({severity})",
        )

    async def seed_normal_transactions(self, count: int = 1000):
        """Generate normal (low risk) transactions."""
        print(f"Seeding {count} normal transactions...")
        merchants = self._refs.get("merchants", [])
        devices = self._refs.get("devices", [])
        locations = self._refs.get("locations", [])
        channels = [c.value for c in TransactionChannel]

        for i in range(count):
            amount = round(random.uniform(5, 500), 2)
            channel = random.choice(channels)
            sender = f"user_{random.randint(1, 100)}"
            receiver = f"user_{random.randint(101, 200)}"
            timestamp = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            tx = self._create_transaction(
                amount=amount,
                channel=channel,
                sender=sender,
                receiver=receiver,
                timestamp=timestamp,
                merchant_id=random.choice(merchants).id if merchants and random.random() > 0.5 else None,
                device_id=random.choice(devices).id if devices and random.random() > 0.5 else None,
                location_id=random.choice(locations).id if locations and random.random() > 0.5 else None,
            )
            self.session.add(tx)
            await self.session.flush()

            # Create low-risk prediction
            risk_score = round(random.uniform(0.01, 0.35), 4)
            pred = self._create_prediction(tx.id, risk_score, "legitimate")
            self.session.add(pred)

            if (i + 1) % 100 == 0:
                print(f"  ... {i + 1}/{count} normal transactions seeded")
                await self.session.flush()

        await self.session.flush()
        print(f"  ✓ {count} normal transactions seeded")

    async def seed_high_amount_fraud(self, count: int = 50):
        """Generate high amount fraud scenarios."""
        print(f"Seeding {count} high amount fraud scenarios...")
        merchants = self._refs.get("merchants", [])
        devices = self._refs.get("devices", [])

        for i in range(count):
            amount = round(random.uniform(5000, 50000), 2)
            sender = f"user_{random.randint(1, 100)}"
            receiver = f"fraud_account_{random.randint(1, 10)}"
            timestamp = datetime.now(timezone.utc) - timedelta(
                hours=random.randint(0, 72),
                minutes=random.randint(0, 59),
            )

            tx = self._create_transaction(
                amount=amount,
                channel="web",
                sender=sender,
                receiver=receiver,
                timestamp=timestamp,
                merchant_id=random.choice(merchants).id if merchants else None,
                device_id=random.choice(devices).id if devices else None,
            )
            self.session.add(tx)
            await self.session.flush()

            # High risk prediction
            risk_score = round(random.uniform(0.75, 0.95), 4)
            pred = self._create_prediction(tx.id, risk_score, "fraud")
            self.session.add(pred)
            await self.session.flush()

            # Create alert
            severity = AlertSeverity.HIGH if risk_score < 0.85 else AlertSeverity.CRITICAL
            alert = self._create_alert(tx.id, risk_score, severity)
            self.session.add(alert)
            await self.session.flush()

            # Create case for critical
            if risk_score >= 0.85:
                case = self._create_case(alert.id, "high")
                self.session.add(case)
                alert.case_id = case.id

        await self.session.flush()
        print(f"  ✓ {count} high amount fraud scenarios seeded")

    async def seed_velocity_fraud(self, count: int = 50):
        """Generate velocity fraud scenarios (many rapid transactions)."""
        print(f"Seeding {count} velocity fraud scenarios...")
        merchants = self._refs.get("merchants", [])

        for i in range(count):
            # Create 10-15 rapid transactions from same sender
            sender = f"user_{random.randint(1, 100)}"
            receiver = f"fraud_account_{random.randint(1, 10)}"
            base_time = datetime.now(timezone.utc) - timedelta(
                hours=random.randint(0, 48),
                minutes=random.randint(0, 59),
            )

            for j in range(random.randint(10, 15)):
                amount = round(random.uniform(100, 1000), 2)
                timestamp = base_time + timedelta(seconds=j * random.randint(10, 30))

                tx = self._create_transaction(
                    amount=amount,
                    channel="mobile_app",
                    sender=sender,
                    receiver=receiver,
                    timestamp=timestamp,
                    merchant_id=random.choice(merchants).id if merchants else None,
                )
                self.session.add(tx)
                await self.session.flush()

                # High risk for velocity
                risk_score = round(random.uniform(0.7, 0.9), 4)
                pred = self._create_prediction(tx.id, risk_score, "fraud")
                self.session.add(pred)

                # Create alert for first transaction in burst
                if j == 0:
                    severity = AlertSeverity.HIGH if risk_score < 0.85 else AlertSeverity.CRITICAL
                    alert = self._create_alert(tx.id, risk_score, severity)
                    self.session.add(alert)
                    await self.session.flush()

                    if risk_score >= 0.85:
                        case = self._create_case(alert.id, "high")
                        self.session.add(case)
                        alert.case_id = case.id

            if (i + 1) % 10 == 0:
                print(f"  ... {i + 1}/{count} velocity fraud scenarios seeded")
                await self.session.flush()

        await self.session.flush()
        print(f"  ✓ {count} velocity fraud scenarios seeded")

    async def seed_location_fraud(self, count: int = 50):
        """Generate suspicious location fraud scenarios."""
        print(f"Seeding {count} location fraud scenarios...")
        locations = self._refs.get("locations", [])

        for i in range(count):
            amount = round(random.uniform(200, 3000), 2)
            sender = f"user_{random.randint(1, 100)}"
            receiver = f"user_{random.randint(101, 200)}"
            timestamp = datetime.now(timezone.utc) - timedelta(
                hours=random.randint(0, 72),
                minutes=random.randint(0, 59),
            )

            tx = self._create_transaction(
                amount=amount,
                channel="web",
                sender=sender,
                receiver=receiver,
                timestamp=timestamp,
                location_id=random.choice(locations).id if locations else None,
            )
            self.session.add(tx)
            await self.session.flush()

            # Medium-high risk
            risk_score = round(random.uniform(0.6, 0.85), 4)
            pred = self._create_prediction(tx.id, risk_score, "suspicious")
            self.session.add(pred)
            await self.session.flush()

            # Create alert
            severity = AlertSeverity.MEDIUM if risk_score < 0.7 else AlertSeverity.HIGH
            alert = self._create_alert(tx.id, risk_score, severity)
            self.session.add(alert)
            await self.session.flush()

            if risk_score >= 0.85:
                case = self._create_case(alert.id, "medium")
                self.session.add(case)
                alert.case_id = case.id

        await self.session.flush()
        print(f"  ✓ {count} location fraud scenarios seeded")

    async def seed_all(self):
        """Run all seeders."""
        print("\n=== Fraud Scenario Seeder ===\n")
        await self._load_references()

        await self.seed_normal_transactions(1000)
        await self.seed_high_amount_fraud(50)
        await self.seed_velocity_fraud(50)
        await self.seed_location_fraud(50)

        print("\n✓ All fraud scenarios seeded successfully!")
