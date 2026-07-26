"""
Prediction API routes.

Provides endpoints for fraud prediction retrieval and explainability.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.identity.user import User
from app.schemas.fraud import ExplanationResponse
from app.services.explainability import ExplainabilityService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get(
    "/{transaction_id}/explanation",
    response_model=ExplanationResponse,
)
async def get_prediction_explanation(
    transaction_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get a human-readable explanation for a transaction's fraud prediction.

    Returns:
        - transaction_id: The transaction UUID
        - risk_score: The calculated risk score (0-1)
        - decision: Final decision (approve, review, reject)
        - reasons: List of human-readable reasons
        - feature_importance: Normalized feature importance breakdown
    """
    explainability_service = ExplainabilityService(session)
    explanation = await explainability_service.get_explanation(transaction_id)

    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found for this transaction",
        )

    return explanation
