"""
Demo analytics data generation module.

This module creates historical analytics data for the FraudWatch platform,
including daily transaction volumes, fraud rates, and other metrics.
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.transaction.transaction import Transaction

from seed.demo.config import config
from seed.demo.helpers import random_timestamp

logger = logging.getLogger(__name__)


async def create_analytics_data(session: AsyncSession) -> Dict[str, int]:
    """Create analytics data for the last N days."""
    logger.info("Creating analytics data...")

    # Get existing transactions
    result = await session.execute(select(Transaction))
    transactions = list(result.scalars().all())

    if not transactions:
        logger.warning("No transactions found for analytics generation")
        return {"analytics_records": 0}

    # Group transactions by date
    transactions_by_date: Dict[Any, List] = {}
    for tx in transactions:
        if tx.transaction_timestamp:
            date_key = tx.transaction_timestamp.date()
            if date_key not in transactions_by_date:
                transactions_by_date[date_key] = []
            transactions_by_date[date_key].append(tx)

    # Create analytics records
    analytics_records = []
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=config.ANALYTICS_DAYS_BACK)

    current_date = start_date
    while current_date <= end_date:
        # Get transactions for this date
        day_transactions = transactions_by_date.get(current_date, [])

        # Calculate metrics
        total_transactions = len(day_transactions)
        total_volume = sum(float(tx.amount) for tx in day_transactions)
        avg_amount = total_volume / total_transactions if total_transactions > 0 else 0

        # Count fraud transactions
        fraud_count = sum(
            1 for tx in day_transactions
            if tx.transaction_metadata and "fraud_pattern" in tx.transaction_metadata
        )
        fraud_rate = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0

        # Create analytics record
        analytics_data: Dict[str, Any] = {
            "date": current_date,
            "total_transactions": total_transactions,
            "total_volume": round(total_volume, 2),
            "average_amount": round(avg_amount, 2),
            "fraud_count": fraud_count,
            "fraud_rate": round(fraud_rate, 2),
            "alert_count": random.randint(max(0, fraud_count - 5), fraud_count + 10),
            "case_count": random.randint(max(0, fraud_count // 3), fraud_count // 2) if fraud_count > 0 else 0,
            "metadata": {
                "by_channel": {},
                "by_payment_method": {},
                "by_status": {},
            }
        }

        analytics_records.append(analytics_data)
        current_date += timedelta(days=1)

    # Note: Analytics model may not exist yet, so we'll just log
    logger.info(f"Generated {len(analytics_records)} analytics records")

    # If Analytics model exists, insert records
    try:
        from app.models.analytics.analytics import Analytics

        for record in analytics_records:
            analytics = Analytics(
                date=record["date"],
                total_transactions=record["total_transactions"],
                total_volume=record["total_volume"],
                average_amount=record["average_amount"],
                fraud_count=record["fraud_count"],
                fraud_rate=record["fraud_rate"],
                alert_count=record["alert_count"],
                case_count=record["case_count"],
                metadata=record["metadata"],
            )
            session.add(analytics)

        await session.flush()
        logger.info(f"Inserted {len(analytics_records)} analytics records")
    except ImportError:
        logger.info("Analytics model not found - analytics data prepared but not inserted")

    return {"analytics_records": len(analytics_records)}


async def create_dashboard_metrics(session: AsyncSession) -> Dict[str, Any]:
    """Create dashboard metrics summary."""
    logger.info("Creating dashboard metrics...")

    # Get transaction statistics
    result = await session.execute(
        select(
            func.count(Transaction.id).label("total_transactions"),
            func.sum(Transaction.amount).label("total_volume"),
            func.avg(Transaction.amount).label("avg_amount"),
        )
    )
    stats = result.one()

    # Get fraud statistics
    from app.models.fraud.fraud_alert import FraudAlert
    from app.models.fraud.fraud_case import FraudCase

    alert_result = await session.execute(select(func.count(FraudAlert.id)))
    total_alerts = alert_result.scalar_one()

    case_result = await session.execute(select(func.count(FraudCase.id)))
    total_cases = case_result.scalar_one()

    metrics: Dict[str, Any] = {
        "total_transactions": stats.total_transactions or 0,
        "total_volume": float(stats.total_volume) if stats.total_volume else 0.0,
        "average_amount": float(stats.avg_amount) if stats.avg_amount else 0.0,
        "total_alerts": total_alerts or 0,
        "total_cases": total_cases or 0,
        "fraud_rate": 0.0,  # Calculated dynamically
    }

    logger.info(f"Dashboard metrics: {metrics}")
    return metrics
