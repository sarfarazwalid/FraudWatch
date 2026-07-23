"""
Dashboard API routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.identity.user import User
from app.models.transaction.transaction import Transaction
from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.fraud_case import FraudCase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get dashboard statistics for the authenticated user.
    """
    # Total transactions
    total_tx_result = await session.execute(
        select(func.count(Transaction.id))
    )
    total_transactions = total_tx_result.scalar() or 0

    # Today's transactions
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_tx_result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.created_at >= today_start
        )
    )
    today_transactions = today_tx_result.scalar() or 0

    # Fraud alerts count
    alerts_result = await session.execute(
        select(func.count(FraudAlert.id))
    )
    fraud_alerts = alerts_result.scalar() or 0

    # Cases count
    total_cases_result = await session.execute(
        select(func.count(FraudCase.id))
    )
    total_cases = total_cases_result.scalar() or 0

    # Open cases
    open_cases_result = await session.execute(
        select(func.count(FraudCase.id)).where(
            FraudCase.status.notin_(["resolved", "closed"])
        )
    )
    open_cases = open_cases_result.scalar() or 0

    # Resolved cases
    resolved_cases_result = await session.execute(
        select(func.count(FraudCase.id)).where(
            FraudCase.status.in_(["resolved", "closed"])
        )
    )
    resolved_cases = resolved_cases_result.scalar() or 0

    # Average risk score (use risk_level_id as proxy if risk_score doesn't exist)
    avg_risk_score = 0.0
    try:
        avg_risk_result = await session.execute(
            select(func.avg(Transaction.risk_score))
        )
        avg_risk_score = float(avg_risk_result.scalar() or 0.0)
    except Exception:
        pass

    # Fraud rate
    fraud_rate = 0.0
    try:
        fraud_count_result = await session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.risk_score >= 0.7
            )
        )
        fraud_count = fraud_count_result.scalar() or 0
        fraud_rate = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0.0
    except Exception:
        pass

    # Transactions per minute (last hour average)
    from datetime import timedelta
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    hour_tx_result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.created_at >= one_hour_ago
        )
    )
    hour_tx_count = hour_tx_result.scalar() or 0
    transactions_per_minute = round(hour_tx_count / 60, 2)

    return {
        "total_transactions": total_transactions,
        "today_transactions": today_transactions,
        "fraud_alerts": fraud_alerts,
        "open_cases": open_cases,
        "resolved_cases": resolved_cases,
        "total_cases": total_cases,
        "avg_risk_score": round(avg_risk_score, 2),
        "transactions_per_minute": transactions_per_minute,
        "fraud_rate": round(fraud_rate, 2),
        "recent_transactions": [],
        "recent_alerts": [],
        "recent_investigations": [],
        "system_health": {
            "status": "healthy",
            "uptime": 0,
            "database": "connected",
            "api": "healthy",
            "ml_service": "unknown",
        },
        "latest_model": None,
        "model_accuracy": 0.0,
        "prediction_latency": 0.0,
    }
