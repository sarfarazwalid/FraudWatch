"""Transaction API routes."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilters, TransactionStatistics
from app.schemas.fraud import FraudAnalysisRequest, FraudAnalysisResponse
from app.services.transaction import TransactionService
from app.models.identity.user import User
from app.repositories.transaction import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/")
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    items, total = await service.get_transactions(
        page=page, page_size=page_size, search=search,
        merchant_id=merchant_id, status_id=status_id, risk_level_id=risk_level_id,
        payment_method_id=payment_method_id, transaction_type_id=transaction_type_id,
        device_id=device_id, location_id=location_id,
        amount_min=amount_min, amount_max=amount_max,
        date_from=date_from, date_to=date_to,
        sort_by=sort_by, sort_order=sort_order,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/{id}")
async def get_transaction(
    id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    item = await service.get_transaction(id)
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return item

@router.get("/statistics/overview")
async def get_statistics(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    return await service.get_statistics()

@router.post("/")
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    return await service.create_transaction(data, user_id=str(current_user.id))

@router.post("/analyze", response_model=FraudAnalysisResponse)
async def analyze_transaction(
    data: FraudAnalysisRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a transaction and immediately perform fraud analysis.

    Workflow:
    1. Creates transaction record
    2. Extracts fraud features (amount, velocity, device, location, merchant)
    3. Runs rule engine evaluation
    4. Runs ML prediction (with fallback scoring)
    5. Creates alert if risk_score >= 0.7
    6. Creates case if risk_score >= 0.85

    Returns:
        FraudAnalysisResponse with transaction, prediction, rules, alert, case
    """
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    return await service.create_transaction_with_fraud_check(data, current_user)

@router.patch("/{id}")
async def update_transaction(
    id: str,
    data: TransactionUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    item = await service.update_transaction(id, data, user_id=str(current_user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return item

@router.delete("/{id}")
async def delete_transaction(
    id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    transaction_repo = TransactionRepository(session)
    service = TransactionService(transaction_repo)
    result = await service.delete_transaction(id, user_id=str(current_user.id))
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}
