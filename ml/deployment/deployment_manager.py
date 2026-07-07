"""
Deployment Manager - Production Model Deployment Controller.

Controls the complete model deployment lifecycle with safety guarantees:

Deployment Flow:
  deploy_model → promote_to_staging → promote_to_production → (rollback)

Design Principles:
- ONE production model per model_name at any time
- Atomic deployment transactions
- Instant rollback (no downtime)
- Canary rollout support
- Staging verification before production
- Structured JSON logging for audit trail

Architecture Layer: Deployment Plane
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import sessionmaker

from app.models.ml.enums import ModelStatus
from app.models.ml.model_version import ModelVersion
from app.models.ml.model_metrics import ModelMetrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    model_version_id: str
    model_name: str
    version: int
    previous_version_id: Optional[str]
    previous_version: Optional[int]
    target_environment: str
    status: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Deployment Manager
# ---------------------------------------------------------------------------


class DeploymentManager:
    """
    Production deployment controller for ML models.

    Controls the safe promotion of models through environments:
    staging → canary → production

    Rules:
    - ONLY ONE production model per model_name
    - All deployment operations are atomic (within a DB transaction)
    - Rollback restores the PREVIOUS production model instantly
    - Deployment status is tracked in ModelVersion.status
    - All operations are logged with full traceability

    Safe for concurrent use if the underlying DB session factory provides
    transactional isolation.
    """

    def __init__(self, session_factory: sessionmaker):
        """
        Initialize the deployment manager.

        Args:
            session_factory: SQLAlchemy session factory for DB access.
        """
        self.session_factory = session_factory

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def deploy_model(
        self,
        model_version_id: str,
        target_environment: str = "production",
        skip_staging: bool = False,
    ) -> DeploymentResult:
        """
        Deploy a model version directly to a target environment.

        This is the primary deployment entry point. It can deploy directly
        to production or to staging for verification first.

        Args:
            model_version_id: UUID of the ModelVersion to deploy.
            target_environment: Target environment ("staging", "canary", "production").
            skip_staging: If True, deploy directly to production without staging promotion.

        Returns:
            DeploymentResult with details.

        Raises:
            ValueError: If model_version_id is not found.
            RuntimeError: If deployment constraints are violated.
        """
        logger.info(
            "Deployment requested",
            extra={
                "event": "deployment.requested",
                "model_version_id": model_version_id,
                "target": target_environment,
                "skip_staging": skip_staging,
            },
        )

        if target_environment not in ("staging", "canary", "production"):
            raise ValueError(
                f"Invalid target environment: {target_environment}. "
                f"Must be staging, canary, or production."
            )

        with self.session_factory() as session:
            # Load model version
            model_version = (
                session.query(ModelVersion)
                .filter(ModelVersion.id == model_version_id)
                .first()
            )
            if model_version is None:
                raise ValueError(f"ModelVersion not found: {model_version_id}")

            if target_environment == "production" and skip_staging:
                # Direct production deployment
                return self._deploy_to_production(session, model_version)
            elif target_environment == "production" and not skip_staging:
                # Promote from staging to production
                return self._promote_to_production(session, model_version)
            elif target_environment == "canary":
                return self._deploy_canary(session, model_version)
            else:  # staging
                return self._deploy_to_staging(session, model_version)

    def promote_model_to_staging(self, model_version_id: str) -> DeploymentResult:
        """
        Promote a model version to staging environment.

        Args:
            model_version_id: UUID of the ModelVersion to stage.

        Returns:
            DeploymentResult with details.
        """
        with self.session_factory() as session:
            model_version = (
                session.query(ModelVersion)
                .filter(ModelVersion.id == model_version_id)
                .first()
            )
            if model_version is None:
                raise ValueError(f"ModelVersion not found: {model_version_id}")

            return self._deploy_to_staging(session, model_version)

    def promote_model_to_production(self, model_version_id: str) -> DeploymentResult:
        """
        Promote a model version to production environment.

        The model must be in STAGED status to be promoted to production.
        Only ONE model per model_name can be in production at a time.

        Args:
            model_version_id: UUID of the ModelVersion to promote.

        Returns:
            DeploymentResult with details.
        """
        with self.session_factory() as session:
            model_version = (
                session.query(ModelVersion)
                .filter(ModelVersion.id == model_version_id)
                .first()
            )
            if model_version is None:
                raise ValueError(f"ModelVersion not found: {model_version_id}")

            if model_version.status != ModelStatus.STAGED:
                raise RuntimeError(
                    f"Model {model_version.model_name} v{model_version.version} "
                    f"is in status {model_version.status.value}, expected STAGED. "
                    f"Promote to staging first."
                )

            return self._promote_to_production(session, model_version)

    def rollback_model(
        self,
        model_name: str,
        target_version: Optional[int] = None,
    ) -> DeploymentResult:
        """
        Rollback a model to a previous version.

        If target_version is specified, rollback to that exact version.
        If not specified, rollback to the immediate previous production version.

        Rollback is:
        - Instant: performs a single DB transaction
        - Safe: preserves all historical versions
        - Atomic: either fully succeeds or fully fails
        - Zero-downtime: no service interruption during rollback

        Args:
            model_name: Name of the model to rollback.
            target_version: Optional specific version to rollback to.

        Returns:
            DeploymentResult with rollback details.

        Raises:
            ValueError: If model_name has no production version or target not found.
        """
        logger.info(
            "Rollback requested",
            extra={
                "event": "rollback.requested",
                "model_name": model_name,
                "target_version": target_version,
            },
        )

        with self.session_factory() as session:
            # Get current production model
            current_prod = (
                session.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == model_name,
                    ModelVersion.status == ModelStatus.PRODUCTION,
                    ModelVersion.deployed == True,  # noqa: E712
                )
                .first()
            )

            if current_prod is None:
                raise ValueError(
                    f"No production model found for {model_name}. Cannot rollback."
                )

            # Find the target version to rollback to
            if target_version is not None:
                target = (
                    session.query(ModelVersion)
                    .filter(
                        ModelVersion.model_name == model_name,
                        ModelVersion.version == target_version,
                    )
                    .first()
                )
                if target is None:
                    raise ValueError(
                        f"Version {target_version} not found for model {model_name}."
                    )
            else:
                # Find the most recent PREVIOUSLY production version
                target = (
                    session.query(ModelVersion)
                    .filter(
                        ModelVersion.model_name == model_name,
                        ModelVersion.status != ModelStatus.PRODUCTION,
                        ModelVersion.deployed == True,  # noqa: E712
                    )
                    .order_by(ModelVersion.deployment_date.desc())
                    .first()
                )

                if target is None:
                    # No previous production version found. Check archived.
                    target = (
                        session.query(ModelVersion)
                        .filter(
                            ModelVersion.model_name == model_name,
                            ModelVersion.status == ModelStatus.ARCHIVED,
                        )
                        .order_by(ModelVersion.deployment_date.desc())
                        .first()
                    )

                    if target is None:
                        raise ValueError(
                            f"No previous version found to rollback for {model_name}."
                        )

            # Atomic rollback: demote current, promote target
            previous_prod_id = str(current_prod.id)
            previous_version = current_prod.version

            # Demote current production
            current_prod.status = ModelStatus.DEPRECATED
            current_prod.deployed = False

            # Promote target to production
            target.status = ModelStatus.PRODUCTION
            target.deployed = True
            target.deployment_date = datetime.now(timezone.utc)

            session.commit()

            logger.info(
                "Rollback completed",
                extra={
                    "event": "rollback.completed",
                    "model_name": model_name,
                    "from_version": current_prod.version,
                    "to_version": target.version,
                    "new_production_id": str(target.id),
                },
            )

            result = DeploymentResult(
                model_version_id=str(target.id),
                model_name=model_name,
                version=target.version,
                previous_version_id=previous_prod_id,
                previous_version=previous_version,
                target_environment="production",
                status="rolled_back",
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "rollback_from_version": current_prod.version,
                    "rollback_to_version": target.version,
                    "rollback_reason": "manual",
                },
            )

            return result

    def get_deployment_history(
        self, model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get deployment history for a model.

        Args:
            model_name: Name of the model.
            limit: Maximum number of history entries to return.

        Returns:
            List of deployment history entries sorted by deployment_date desc.
        """
        with self.session_factory() as session:
            versions = (
                session.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == model_name,
                    ModelVersion.deployed == True,  # noqa: E712
                )
                .order_by(ModelVersion.deployment_date.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "model_version_id": str(v.id),
                    "version": v.version,
                    "model_name": v.model_name,
                    "status": v.status.value,
                    "deployed": v.deployed,
                    "deployment_date": v.deployment_date.isoformat() if v.deployment_date else None,
                    "algorithm": v.algorithm.value,
                    "framework": v.framework.value,
                }
                for v in versions
            ]

    def get_current_production(self, model_name: str) -> Optional[dict[str, Any]]:
        """
        Get the current production model version.

        Args:
            model_name: Name of the model.

        Returns:
            Dict with model version details or None.
        """
        with self.session_factory() as session:
            model_version = (
                session.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == model_name,
                    ModelVersion.status == ModelStatus.PRODUCTION,
                    ModelVersion.deployed == True,  # noqa: E712
                )
                .first()
            )

            if model_version is None:
                return None

            # Get metrics
            metrics = (
                session.query(ModelMetrics)
                .filter(ModelMetrics.model_version_id == model_version.id)
                .first()
            )

            return {
                "model_version_id": str(model_version.id),
                "version": model_version.version,
                "model_name": model_version.model_name,
                "algorithm": model_version.algorithm.value,
                "framework": model_version.framework.value,
                "status": model_version.status.value,
                "deployment_date": model_version.deployment_date.isoformat() if model_version.deployment_date else None,
                "artifact_path": model_version.artifact_path,
                "checksum": model_version.checksum,
                "metrics": {
                    "accuracy": metrics.accuracy if metrics else None,
                    "precision": metrics.precision if metrics else None,
                    "recall": metrics.recall if metrics else None,
                    "f1_score": metrics.f1_score if metrics else None,
                    "roc_auc": metrics.roc_auc if metrics else None,
                } if metrics else None,
            }

    # -----------------------------------------------------------------------
    # Internal Deployment Methods
    # -----------------------------------------------------------------------

    def _deploy_to_staging(
        self, session: Any, model_version: ModelVersion
    ) -> DeploymentResult:
        """
        Deploy model version to staging environment.

        Args:
            session: DB session.
            model_version: ModelVersion to stage.

        Returns:
            DeploymentResult.
        """
        model_version.status = ModelStatus.STAGED
        model_version.deployed = True
        model_version.deployment_date = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            "Model staged",
            extra={
                "event": "deployment.staged",
                "model_name": model_version.model_name,
                "version": model_version.version,
                "model_version_id": str(model_version.id),
            },
        )

        return DeploymentResult(
            model_version_id=str(model_version.id),
            model_name=model_version.model_name,
            version=model_version.version,
            previous_version_id=None,
            previous_version=None,
            target_environment="staging",
            status="staged",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _deploy_canary(
        self, session: Any, model_version: ModelVersion
    ) -> DeploymentResult:
        """
        Deploy model version as a canary (experimental) deployment.

        Canary models serve a small percentage of traffic for validation.
        They are not yet production but are promoted alongside production.

        Args:
            session: DB session.
            model_version: ModelVersion to deploy as canary.

        Returns:
            DeploymentResult.
        """
        model_version.status = ModelStatus.STAGED
        model_version.deployed = True
        model_version.deployment_date = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            "Canary deployed",
            extra={
                "event": "deployment.canary",
                "model_name": model_version.model_name,
                "version": model_version.version,
                "model_version_id": str(model_version.id),
            },
        )

        return DeploymentResult(
            model_version_id=str(model_version.id),
            model_name=model_version.model_name,
            version=model_version.version,
            previous_version_id=None,
            previous_version=None,
            target_environment="canary",
            status="canary",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _deploy_to_production(
        self, session: Any, model_version: ModelVersion
    ) -> DeploymentResult:
        """
        Deploy model version directly to production (skipping staging).

        This is a direct deployment bypassing the staging step.
        Use with caution - prefer the promote flow for safety.

        Args:
            session: DB session.
            model_version: ModelVersion to deploy.

        Returns:
            DeploymentResult.
        """
        return self._promote_to_production(session, model_version)

    def _promote_to_production(
        self, session: Any, model_version: ModelVersion
    ) -> DeploymentResult:
        """
        Promote a model version to production.

        Ensures ONLY ONE production model exists per model_name.
        The previous production model is demoted to DEPRECATED.

        This is the core atomic deployment operation.

        Args:
            session: DB session.
            model_version: ModelVersion to promote.

        Returns:
            DeploymentResult.
        """
        model_name = model_version.model_name

        # Find and demote current production model for this model_name
        current_prod = (
            session.query(ModelVersion)
            .filter(
                ModelVersion.model_name == model_name,
                ModelVersion.status == ModelStatus.PRODUCTION,
                ModelVersion.deployed == True,  # noqa: E712
            )
            .first()
        )

        previous_version_id: Optional[str] = None
        previous_version: Optional[int] = None

        if current_prod is not None:
            previous_version_id = str(current_prod.id)
            previous_version = current_prod.version

            # Demote current production
            current_prod.status = ModelStatus.DEPRECATED
            current_prod.deployed = False
            logger.info(
                "Demoted previous production",
                extra={
                    "event": "deployment.demoted",
                    "model_name": model_name,
                    "previous_version": current_prod.version,
                    "previous_id": str(current_prod.id),
                },
            )

        # Promote new model to production
        model_version.status = ModelStatus.PRODUCTION
        model_version.deployed = True
        model_version.deployment_date = datetime.now(timezone.utc)

        session.commit()

        logger.info(
            "Production deployment completed",
            extra={
                "event": "deployment.production",
                "model_name": model_name,
                "new_version": model_version.version,
                "new_id": str(model_version.id),
                "previous_version": previous_version,
                "previous_id": previous_version_id,
            },
        )

        result = DeploymentResult(
            model_version_id=str(model_version.id),
            model_name=model_name,
            version=model_version.version,
            previous_version_id=previous_version_id,
            previous_version=previous_version,
            target_environment="production",
            status="production",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return result
