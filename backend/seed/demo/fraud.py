"""
Demo fraud data generation module.

This module creates fraud alerts and investigation cases based on
the fraudulent transactions generated in the transactions module.
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.investigation_timeline import InvestigationTimeline
from app.models.fraud.fraud_comment import FraudComment
from app.models.fraud.fraud_attachment import FraudAttachment
from app.models.fraud.enums import AlertSeverity, AlertStatus, CasePriority, CaseStatus, DetectionMethod, TimelineActionType, CommentVisibility, AttachmentType
from app.models.identity.user import User

from seed.demo.config import config
from seed.demo.helpers import (
    random_timestamp, generate_alert_number, generate_case_number,
    generate_evidence_json, weighted_choice
)

logger = logging.getLogger(__name__)


async def get_fraud_transactions(session: AsyncSession) -> List[Any]:
    """Get all fraudulent transactions."""
    from app.models.transaction.transaction import Transaction

    result = await session.execute(
        select(Transaction).where(
            Transaction.transaction_metadata.has_key("fraud_pattern")
        )
    )
    return list(result.scalars().all())


async def get_demo_users(session: AsyncSession) -> List[User]:
    """Get demo users for assignment."""
    result = await session.execute(select(User))
    return list(result.scalars().all())


def select_alert_severity() -> AlertSeverity:
    """Select alert severity based on distribution."""
    r = random.random()
    cumulative = 0
    for severity, weight in config.ALERT_SEVERITY_DISTRIBUTION.items():
        cumulative += weight
        if r <= cumulative:
            return AlertSeverity(severity)
    return AlertSeverity.MEDIUM


async def create_fraud_alerts(
    session: AsyncSession,
    fraud_transactions: List[Any],
    users: List[User]
) -> List[FraudAlert]:
    """Create fraud alerts from fraudulent transactions."""
    logger.info("Creating fraud alerts...")

    if not fraud_transactions or not users:
        logger.warning("No fraud transactions or users available for alert creation")
        return []

    alerts = []
    num_alerts = int(len(fraud_transactions) * config.ALERT_RATIO_FROM_FRAUD)

    # Select transactions to create alerts for
    selected_transactions = random.sample(
        fraud_transactions,
        min(num_alerts, len(fraud_transactions))
    )

    alert_titles = [
        "Multiple transactions detected from same device",
        "High value transaction exceeds customer pattern",
        "Suspicious foreign location detected",
        "Impossible travel pattern detected",
        "New device accessing account",
        "Transaction velocity threshold exceeded",
        "Unusual merchant transaction pattern",
        "Account takeover indicators detected",
        "Dormant account activity detected",
        "Round amount laundering pattern",
    ]

    alert_descriptions = [
        "Automated detection system flagged this transaction based on multiple risk factors.",
        "Transaction pattern matches known fraud signatures.",
        "Behavioral analysis indicates anomalous activity.",
        "Risk scoring model identified high-risk characteristics.",
        "Multiple fraud detection rules triggered simultaneously.",
    ]

    for idx, transaction in enumerate(selected_transactions, 1):
        # Get fraud type from metadata
        fraud_type = transaction.transaction_metadata.get("fraud_pattern", "unknown")

        # Determine severity
        severity = select_alert_severity()

        # Determine status (weighted towards new)
        status_weights = {
            AlertStatus.NEW: 0.40,
            AlertStatus.TRIAGED: 0.20,
            AlertStatus.ACKNOWLEDGED: 0.15,
            AlertStatus.ASSIGNED: 0.15,
            AlertStatus.ESCALATED: 0.05,
            AlertStatus.RESOLVED: 0.03,
            AlertStatus.DISMISSED: 0.02,
        }
        status = weighted_choice(
            [{"status": s, "weight": w} for s, w in status_weights.items()],
            "status"
        )["status"]

        # Get risk score from transaction
        risk_score = transaction.transaction_metadata.get("fraud_confidence", random.uniform(0.7, 0.95))
        if isinstance(risk_score, float):
            risk_score = risk_score * 100  # Convert to 0-100 scale
        else:
            risk_score = random.uniform(70, 95)

        # Select detection method
        detection_methods = [
            DetectionMethod.RULE_BASED,
            DetectionMethod.MACHINE_LEARNING,
            DetectionMethod.HYBRID,
        ]
        detection_method = random.choice(detection_methods)

        # Assign analyst
        assigned_analyst = random.choice(users) if random.random() > 0.3 else None

        # Generate timestamps
        generated_at = transaction.transaction_timestamp + timedelta(minutes=random.randint(1, 30))
        acknowledged_at = None
        resolved_at = None

        if status in [AlertStatus.ACKNOWLEDGED, AlertStatus.ASSIGNED, AlertStatus.ESCALATED, AlertStatus.RESOLVED]:
            acknowledged_at = generated_at + timedelta(minutes=random.randint(5, 60))

        if status == AlertStatus.RESOLVED:
            resolved_at = acknowledged_at + timedelta(hours=random.randint(1, 48))

        # Create alert
        alert = FraudAlert(
            alert_number=generate_alert_number(idx),
            title=random.choice(alert_titles),
            description=random.choice(alert_descriptions),
            transaction_id=transaction.id,
            merchant_id=transaction.merchant_id,
            severity=severity,
            status=status,
            detection_method=detection_method,
            risk_score=round(risk_score, 2),
            generated_at=generated_at,
            acknowledged_at=acknowledged_at,
            resolved_at=resolved_at,
            false_positive=status == AlertStatus.FALSE_POSITIVE,
            resolution_summary="Investigation completed - fraud confirmed" if status == AlertStatus.RESOLVED else None,
            assigned_analyst_id=assigned_analyst.id if assigned_analyst else None,
            creator_id=random.choice(users).id if users else None,
        )

        alerts.append(alert)

    # Bulk insert
    if alerts:
        session.add_all(alerts)
        await session.flush()

    logger.info(f"Created {len(alerts)} fraud alerts")
    return alerts


async def create_fraud_cases(
    session: AsyncSession,
    alerts: List[FraudAlert],
    users: List[User]
) -> List[FraudCase]:
    """Create fraud investigation cases from alerts."""
    logger.info("Creating fraud cases...")

    if not alerts or not users:
        logger.warning("No alerts or users available for case creation")
        return []

    # Select alerts to create cases for (60% of alerts)
    num_cases = int(len(alerts) * config.CASE_RATIO_FROM_ALERTS)
    selected_alerts = random.sample(alerts, min(num_cases, len(alerts)))

    cases = []
    investigators = [u for u in users if "investigator" in u.role.name or "admin" in u.role.name]
    if not investigators:
        investigators = users

    case_titles = [
        "Investigation: Suspicious Transaction Activity",
        "Fraud Review: High-Risk Transaction",
        "Case: Account Takeover Investigation",
        "Review: Unusual Transaction Pattern",
        "Investigation: Potential Fraudulent Activity",
    ]

    case_statuses = [
        CaseStatus.NEW,
        CaseStatus.TRIAGED,
        CaseStatus.UNDER_INVESTIGATION,
        CaseStatus.ESCALATED,
        CaseStatus.AWAITING_CUSTOMER,
        CaseStatus.CONFIRMED_FRAUD,
        CaseStatus.FALSE_POSITIVE,
        CaseStatus.RESOLVED,
        CaseStatus.CLOSED,
    ]

    for idx, alert in enumerate(selected_alerts, 1):
        # Get fraud type from alert's transaction
        fraud_type = "unknown"
        if alert.transaction and alert.transaction.transaction_metadata:
            fraud_type = alert.transaction.transaction_metadata.get("fraud_pattern", "unknown")

        # Determine case status
        status = random.choice(case_statuses)

        # Determine priority based on alert severity
        priority_map = {
            AlertSeverity.CRITICAL: CasePriority.CRITICAL,
            AlertSeverity.HIGH: CasePriority.HIGH,
            AlertSeverity.MEDIUM: CasePriority.MEDIUM,
            AlertSeverity.LOW: CasePriority.LOW,
        }
        priority = priority_map.get(alert.severity, CasePriority.MEDIUM)

        # Assign investigator
        investigator = random.choice(investigators) if random.random() > 0.2 else None

        # Generate timestamps
        opened_at = alert.generated_at + timedelta(minutes=random.randint(10, 120)) if alert.generated_at else random_timestamp(start_days_ago=30)
        closed_at = None

        if status in [CaseStatus.RESOLVED, CaseStatus.CLOSED, CaseStatus.CONFIRMED_FRAUD, CaseStatus.FALSE_POSITIVE]:
            closed_at = opened_at + timedelta(days=random.randint(1, 14))

        # Determine if fraud was confirmed
        fraud_confirmed = status in [CaseStatus.CONFIRMED_FRAUD, CaseStatus.RESOLVED]

        # Calculate loss amount
        loss_amount = None
        if fraud_confirmed and alert.transaction:
            loss_amount = float(alert.transaction.amount) * random.uniform(0.8, 1.0)

        # Generate evidence
        evidence = generate_evidence_json(fraud_type)

        # Create case
        case = FraudCase(
            case_number=generate_case_number(idx),
            alert_id=alert.id,
            investigator_id=investigator.id if investigator else None,
            assigned_to=random.choice(users).id if users else None,
            merchant_id=alert.merchant_id,
            severity=alert.severity.value,
            priority=priority,
            status=status,
            escalation_level=random.randint(0, 3) if status == CaseStatus.ESCALATED else 0,
            opened_at=opened_at,
            closed_at=closed_at,
            fraud_confirmed=fraud_confirmed,
            loss_amount=loss_amount,
            resolution=random.choice(["fraud_confirmed", "false_positive", "resolved", "closed"]) if closed_at else None,
            summary=f"Investigation of {fraud_type.replace('_', ' ')} pattern. Case reviewed and {status.replace('_', ' ')}.",
        )

        cases.append(case)

        # Add timeline entry
        if cases:
            timeline_entry = InvestigationTimeline(
                case_id=case.id,
                action=TimelineActionType.CREATED,
                description="Case created from fraud alert",
                performed_by=investigator.id if investigator else None,
                performed_at=opened_at,
            )
            session.add(timeline_entry)

        # Add some comments
        if random.random() > 0.5:
            comment = FraudComment(
                case_id=case.id,
                content=f"Initial review completed. {random.choice(['Suspicious activity confirmed.', 'Requires further investigation.', 'Customer contacted for verification.'])}",
                visibility=CommentVisibility.INTERNAL,
                created_by=investigator.id if investigator else None,
            )
            session.add(comment)

    # Bulk insert
    if cases:
        session.add_all(cases)
        await session.flush()

    logger.info(f"Created {len(cases)} fraud cases")
    return cases


async def create_fraud_data(session: AsyncSession) -> Dict[str, int]:
    """Create all fraud-related demo data."""
    logger.info("Starting fraud data generation...")

    # Get fraudulent transactions
    fraud_transactions = await get_fraud_transactions(session)
    logger.info(f"Found {len(fraud_transactions)} fraudulent transactions")

    if not fraud_transactions:
        logger.warning("No fraudulent transactions found. Skipping fraud data generation.")
        return {"alerts": 0, "cases": 0}

    # Get demo users
    users = await get_demo_users(session)
    logger.info(f"Found {len(users)} users")

    # Create alerts
    alerts = await create_fraud_alerts(session, fraud_transactions, users)

    # Create cases
    cases = await create_fraud_cases(session, alerts, users)

    return {
        "alerts": len(alerts),
        "cases": len(cases),
    }
