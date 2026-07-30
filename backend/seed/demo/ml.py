import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.ml.model_version import ModelVersion
from app.models.ml.training_run import TrainingRun
from app.models.ml.model_metrics import ModelMetrics
from app.models.ml.feature_importance import FeatureImportance
from app.models.ml.prediction_history import PredictionHistory
from app.models.ml.model_registry import ModelRegistry
from app.models.ml.enums import ModelStatus, AlgorithmType, FrameworkType, TrainingStatus, PredictionStatus
from app.models.identity.user import User

from seed.demo.config import config
from seed.demo.helpers import random_timestamp

logger = logging.getLogger(__name__)


async def get_demo_users(session: AsyncSession) -> List[User]:
    """Get demo users."""
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def create_model_versions(session: AsyncSession, users: List[User]) -> List[ModelVersion]:
    """Create ML model versions."""
    logger.info("Creating ML model versions...")

    model_versions = []

    for model_config in config.ML_MODELS:
        model_name = model_config["name"]
        num_versions = model_config["versions"]
        current_version = model_config["current_version"]

        for version_num in range(1, num_versions + 1):
            # Determine status
            if version_num == current_version:
                status = ModelStatus.PRODUCTION if model_config["status"] == "production" else ModelStatus.STAGED
                deployed = True
                deployment_date = random_timestamp(start_days_ago=30, end_days_ago=1)
            elif version_num == current_version - 1:
                status = ModelStatus.ARCHIVED
                deployed = False
                deployment_date = None
            else:
                status = random.choice([ModelStatus.DRAFT, ModelStatus.ARCHIVED, ModelStatus.DEPRECATED])
                deployed = False
                deployment_date = None

            # Create model version
            model_version = ModelVersion(
                model_name=model_name,
                version=version_num,
                algorithm=AlgorithmType(model_config["algorithm"]),
                framework=FrameworkType(model_config["framework"]),
                artifact_path=f"/models/{model_name.lower().replace(' ', '_')}/v{version_num}/model.pkl",
                checksum=f"{random.randint(0, 0xFFFFFFFF):08x}{random.randint(0, 0xFFFFFFFF):08x}",
                status=status,
                deployed=deployed,
                deployment_date=deployment_date,
                description=f"{model_name} version {version_num}",
                hyperparameters='{"learning_rate": 0.01, "max_depth": 6, "n_estimators": 100}',
                training_duration_seconds=random.randint(300, 3600),
            )

            model_versions.append(model_version)

    # Bulk insert
    if model_versions:
        session.add_all(model_versions)
        await session.flush()

    logger.info(f"Created {len(model_versions)} model versions")
    return model_versions


async def create_training_runs(session: AsyncSession, model_versions: List[ModelVersion], users: List[User]) -> List[TrainingRun]:
    """Create training runs for model versions."""
    logger.info("Creating training runs...")

    if not model_versions or not users:
        return []

    training_runs = []

    # Create training runs for production models
    for model_version in model_versions:
        if model_version.status in [ModelStatus.PRODUCTION, ModelStatus.STAGED, ModelStatus.ARCHIVED]:
            # Create training run
            training_run = TrainingRun(
                model_version_id=model_version.id,
                run_name=f"Training run for {model_version.model_name} v{model_version.version}",
                status=TrainingStatus.COMPLETED,
                started_at=model_version.created_at - timedelta(seconds=model_version.training_duration_seconds or 600),
                completed_at=model_version.created_at,
                dataset_size=random.randint(10000, 1000000),
                training_samples=random.randint(8000, 800000),
                validation_samples=random.randint(1000, 100000),
                test_samples=random.randint(1000, 100000),
                hyperparameters='{"learning_rate": 0.01, "max_depth": 6, "n_estimators": 100}',
                artifacts_path=model_version.artifact_path,
                executed_by=random.choice(users).id if users else None,
            )

            training_runs.append(training_run)

    # Bulk insert
    if training_runs:
        session.add_all(training_runs)
        await session.flush()

    logger.info(f"Created {len(training_runs)} training runs")
    return training_runs


async def create_model_metrics(session: AsyncSession, model_versions: List[ModelVersion]) -> List[ModelMetrics]:
    """Create model metrics for model versions."""
    logger.info("Creating model metrics...")

    if not model_versions:
        return []

    model_metrics = []

    for model_version in model_versions:
        if model_version.status in [ModelStatus.PRODUCTION, ModelStatus.STAGED]:
            # Get metrics from config if available
            model_config = None
            for config_model in config.ML_MODELS:
                if config_model["name"] == model_version.model_name:
                    model_config = config_model
                    break

            if model_config:
                accuracy = model_config["accuracy"]
                precision = model_config["precision"]
                recall = model_config["recall"]
                f1_score = model_config["f1_score"]
                roc_auc = model_config["roc_auc"]
            else:
                # Generate random metrics
                accuracy = random.uniform(0.85, 0.98)
                precision = random.uniform(0.80, 0.95)
                recall = random.uniform(0.75, 0.93)
                f1_score = 2 * (precision * recall) / (precision + recall)
                roc_auc = random.uniform(0.90, 0.99)

            metrics = ModelMetrics(
                model_version_id=model_version.id,
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1_score, 4),
                roc_auc=round(roc_auc, 4),
                confusion_matrix={
                    "true_positive": random.randint(800, 900),
                    "false_positive": random.randint(20, 80),
                    "true_negative": random.randint(9000, 9500),
                    "false_negative": random.randint(50, 150),
                },
                additional_metrics={
                    "log_loss": round(random.uniform(0.1, 0.3), 4),
                    "mcc": round(random.uniform(0.85, 0.95), 4),
                },
            )

            model_metrics.append(metrics)

    # Bulk insert
    if model_metrics:
        session.add_all(model_metrics)
        await session.flush()

    logger.info(f"Created {len(model_metrics)} model metrics")
    return model_metrics


async def create_feature_importance(session: AsyncSession, model_versions: List[ModelVersion]) -> List[FeatureImportance]:
    """Create feature importance for model versions."""
    logger.info("Creating feature importance data...")

    if not model_versions:
        return []

    feature_importances = []

    for model_version in model_versions:
        if model_version.status in [ModelStatus.PRODUCTION, ModelStatus.STAGED]:
            # Create feature importance entries
            for idx, (feature_name, importance) in enumerate(config.TOP_FRAUD_FEATURES, 1):
                feature_importance = FeatureImportance(
                    model_version_id=model_version.id,
                    feature_name=feature_name,
                    importance_score=importance,
                    feature_type="numerical",
                    rank=idx,
                )
                feature_importances.append(feature_importance)

    # Bulk insert
    if feature_importances:
        session.add_all(feature_importances)
        await session.flush()

    logger.info(f"Created {len(feature_importances)} feature importance entries")
    return feature_importances


async def create_prediction_history(session: AsyncSession, model_versions: List[ModelVersion], num_transactions: int) -> List[PredictionHistory]:
    """Create prediction history using direct SQL for transaction IDs."""
    logger.info("Creating prediction history...")
    from uuid import uuid4

    if not model_versions:
        return []

    # Get production models
    production_models = [mv for mv in model_versions if mv.deployed]
    if not production_models:
        production_models = [model_versions[0]] if model_versions else []

    # Get transaction IDs from database
    result = await session.execute(text("SELECT id, is_fraud FROM transactions WHERE is_fraud IS NOT NULL LIMIT 10000"))
    tx_rows = result.fetchall()
    if not tx_rows:
        logger.warning("No transactions found for prediction history")
        return []

    prediction_histories = []
    for idx, (tx_id, is_fraud) in enumerate(tx_rows, 1):
        model_version = random.choice(production_models)

        if is_fraud:
            prediction_result = random.choice(["fraud", "suspicious"])
            confidence_score = random.uniform(0.7, 0.99)
        else:
            prediction_result = random.choice(["legitimate", "legitimate", "legitimate", "suspicious"])
            confidence_score = random.uniform(0.6, 0.95)

        prediction = PredictionHistory(
            prediction_id=f"PRED-{idx:08d}",
            transaction_id=tx_id,
            model_version_id=model_version.id,
            prediction_timestamp=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 1000)),
            latency_ms=random.randint(10, 500),
            status=PredictionStatus.COMPLETED,
            input_features_hash=f"{random.randint(0, 0xFFFFFFFF):08x}",
            prediction_result=prediction_result,
            confidence_score=round(confidence_score, 4),
        )

        prediction_histories.append(prediction)

    # Bulk insert
    if prediction_histories:
        session.add_all(prediction_histories)
        await session.flush()

    logger.info(f"Created {len(prediction_histories)} prediction history entries")
    return prediction_histories


async def create_model_registry(session: AsyncSession, model_versions: List[ModelVersion], users: List[User]) -> List[ModelRegistry]:
    """Create model registry entries."""
    logger.info("Creating model registry entries...")

    if not model_versions or not users:
        return []

    # Group model versions by model name
    model_groups = {}
    for mv in model_versions:
        if mv.model_name not in model_groups:
            model_groups[mv.model_name] = []
        model_groups[mv.model_name].append(mv)

    registries = []

    for model_name, versions in model_groups.items():
        # Sort by version
        versions.sort(key=lambda x: x.version)

        # Find current version
        current_version = None
        for mv in versions:
            if mv.deployed and mv.status == ModelStatus.PRODUCTION:
                current_version = mv
                break

        if not current_version and versions:
            current_version = versions[-1]

        if current_version:
            # Find previous version
            previous_version = None
            for mv in reversed(versions):
                if mv.version < current_version.version:
                    previous_version = mv
                    break

            registry = ModelRegistry(
                model_name=model_name,
                current_version=current_version.version,
                previous_version=previous_version.version if previous_version else None,
                rollback_version=previous_version.version if previous_version else None,
                deployment_environment="production",
                deployed_at=current_version.deployment_date,
                deployed_by=random.choice(users).id if users else None,
                active=True,
                deployment_notes=f"Production deployment of {model_name} v{current_version.version}",
            )

            registries.append(registry)

    # Bulk insert
    if registries:
        session.add_all(registries)
        await session.flush()

    logger.info(f"Created {len(registries)} model registry entries")
    return registries


async def create_ml_data(session: AsyncSession, num_transactions: int) -> Dict[str, int]:
    """Create all ML-related demo data."""
    logger.info("Starting ML data generation...")

    # Get users
    users = await get_demo_users(session)

    # Create model versions
    model_versions = await create_model_versions(session, users)

    # Create training runs
    training_runs = await create_training_runs(session, model_versions, users)

    # Create model metrics
    model_metrics = await create_model_metrics(session, model_versions)

    # Create feature importance
    feature_importances = await create_feature_importance(session, model_versions)

    # Create prediction history
    prediction_histories = await create_prediction_history(session, model_versions, num_transactions)

    # Create model registry
    model_registries = await create_model_registry(session, model_versions, users)

    return {
        "model_versions": len(model_versions),
        "training_runs": len(training_runs),
        "model_metrics": len(model_metrics),
        "feature_importances": len(feature_importances),
        "prediction_histories": len(prediction_histories),
        "model_registries": len(model_registries),
    }
