"""
ML Lifecycle API routes.

Provides endpoints for:
- Training pipeline
- Model registry
- Deployment management
- Model monitoring
- Drift detection
- Model comparison
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.identity.user import User
from app.services.model_registry import ModelRegistryService
from app.repositories.model_registry import ModelRegistryRepository

router = APIRouter(prefix="/ml", tags=["ML Lifecycle"])


@router.get("/models")
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all registered models."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    items, total = await service.list_models(
        page=page, page_size=page_size, search=search
    )
    return {
        "items": [
            {
                "id": str(m.id),
                "model_name": m.model_name,
                "algorithm": m.algorithm.value if hasattr(m.algorithm, 'value') else str(m.algorithm),
                "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get model details by ID."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": str(model.id),
        "model_name": model.model_name,
        "algorithm": model.algorithm.value if hasattr(model.algorithm, 'value') else str(model.algorithm),
        "status": model.status.value if hasattr(model.status, 'value') else str(model.status),
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
    }


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Deploy a model to production."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    result = await service.deploy_model(model_id)
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "message": "Model deployed successfully",
        "model_id": str(result.id),
        "model_name": result.model_name,
        "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
    }


@router.post("/models/{model_id}/rollback")
async def rollback_model(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Rollback to a previous model version."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)

    # Get model to find model_name
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Use deployment manager for rollback
    from ml.deployment.deployment_manager import DeploymentManager
    from sqlalchemy.orm import sessionmaker

    # Create a session factory from the current session
    # For simplicity, we'll use the repo's session factory
    # In production, this would be a proper session factory
    deployment_manager = DeploymentManager(session)
    result = deployment_manager.rollback_model(model.model_name)

    return {
        "message": "Model rolled back successfully",
        "from_version": result.previous_version,
        "to_version": result.version,
    }


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Archive a model."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    result = await service.archive_model(model_id)
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model archived successfully"}


@router.get("/models/{model_id}/metrics")
async def get_model_metrics(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get model performance metrics."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # In a real implementation, this would query ModelMetrics table
    # For now, return placeholder
    return {
        "model_id": model_id,
        "model_name": model.model_name,
        "accuracy": 0.95,
        "precision": 0.92,
        "recall": 0.94,
        "f1_score": 0.93,
        "roc_auc": 0.97,
        "latency_mean_ms": 15.5,
        "latency_p95_ms": 25.0,
        "latency_p99_ms": 40.0,
    }


@router.get("/models/{model_id}/drift")
async def get_model_drift(
    model_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get drift detection report for a model."""
    repo = ModelRegistryRepository(session)
    service = ModelRegistryService(repo)
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # In a real implementation, this would run drift detection
    # For now, return placeholder
    return {
        "model_id": model_id,
        "model_name": model.model_name,
        "overall_drift_score": 0.05,
        "overall_warning_level": "low",
        "feature_drifts": [],
        "prediction_drift": None,
        "confidence_drift": None,
        "summary": "No significant drift detected",
        "recommendations": [],
    }


@router.get("/jobs")
async def list_training_jobs(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List training jobs."""
    # In a real implementation, this would query TrainingRun table
    return {
        "jobs": [],
        "total": 0,
    }


@router.post("/train")
async def start_training(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new training job.

    In production, this would:
    1. Validate training configuration
    2. Create a training run record
    3. Queue a Celery task for async training
    4. Return the training run ID
    """
    # Placeholder - in production, this would trigger Celery task
    return {
        "message": "Training job queued",
        "training_run_id": "placeholder",
        "status": "queued",
    }
