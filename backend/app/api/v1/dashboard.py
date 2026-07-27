"""
Dashboard API routes.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.identity.user import User
from app.models.transaction.transaction import Transaction
from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.fraud_case import FraudCase
from app.models.fraud.enums import CaseStatus

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

    # Open cases (not CLOSED or RESOLVED)
    open_cases_result = await session.execute(
        select(func.count(FraudCase.id)).where(
            FraudCase.status.notin_([CaseStatus.CLOSED, CaseStatus.RESOLVED])
        )
    )
    open_cases = open_cases_result.scalar() or 0

    # Resolved cases
    resolved_cases_result = await session.execute(
        select(func.count(FraudCase.id)).where(
            FraudCase.status.in_([CaseStatus.RESOLVED, CaseStatus.CLOSED])
        )
    )
    resolved_cases = resolved_cases_result.scalar() or 0

    # Average risk score from fraud alerts
    avg_risk_result = await session.execute(
        select(func.avg(FraudAlert.risk_score))
    )
    avg_risk_score = float(avg_risk_result.scalar() or 0.0)

    # Fraud rate: alerts with risk_score >= 70 (0-100 scale) / total transactions
    fraud_rate = 0.0
    if total_transactions > 0:
        high_risk_alerts_result = await session.execute(
            select(func.count(FraudAlert.id)).where(
                FraudAlert.risk_score >= 70
            )
        )
        high_risk_count = high_risk_alerts_result.scalar() or 0
        fraud_rate = (high_risk_count / total_transactions * 100)

    # Transactions per minute (last hour average)
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
