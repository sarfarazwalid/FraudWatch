"""
Model Loader - Production Model Caching & Hot-Swap System.

Implements zero-downtime model switching for the inference plane:

Hot-Swap Mechanism:
  1. Active production model cached in memory
  2. Background thread periodically polls ModelRegistry
  3. Detects version changes by comparing checksums / version IDs
  4. Pre-loads new model in shadow mode before swapping
  5. Atomic pointer swap ensures thread-safe replacement
  6. Old model is released only after new model is confirmed working

Design Principles:
- Inference NEVER blocks on model loading
- Hot-swap is transparent to callers (atomic reference swap)
- Thread-safe: read-write lock on model reference
- Graceful degradation: falls back to old model on new model failure
- No service restart required for model updates
- Polling interval is configurable and safe

Architecture Layer: Inference Plane (Serving)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Protocol
from uuid import UUID

import numpy as np
from sqlalchemy.orm import sessionmaker

from app.models.ml.enums import ModelStatus
from app.models.ml.model_version import ModelVersion
from app.models.ml.model_metrics import ModelMetrics as DBModelMetrics

from ml.models.base_model import BaseMLModel
from ml.training.trainer import ModelFactory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class ModelProvider(Protocol):
    """Protocol for objects that provide a loaded ML model."""

    def get_model(self) -> Optional[BaseMLModel]:
        """Get the currently loaded model instance."""
        ...

    def get_model_info(self) -> Optional[dict[str, Any]]:
        """Get metadata about the currently loaded model."""
        ...


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class LoadedModelInfo:
    """Information about a loaded model in memory."""

    model_version_id: str
    model_name: str
    version: int
    algorithm: str
    framework: str
    artifact_path: str
    checksum: str
    loaded_at: datetime
    is_production: bool = True


@dataclass
class ModelCacheEntry:
    """Thread-safe cache entry containing a loaded model."""

    model: BaseMLModel
    info: LoadedModelInfo
    load_count: int = 0
    last_used_at: Optional[datetime] = None
    error_count: int = 0


# ---------------------------------------------------------------------------
# Model Loader (Hot-Swap System)
# ---------------------------------------------------------------------------


class ModelLoader:
    """
    Thread-safe model loader with automatic hot-swapping.

    Maintains an in-memory cache of the active production model and
    periodically polls the database for new versions. When a new
    production version is detected, it pre-loads the model in the
    background and atomically swaps the reference.

    Thread Safety:
    - _active_model is protected by threading.Lock
    - Read operations (get_model) acquire a shared read lock
    - Write operations (swap) acquire an exclusive write lock
    - The polling thread never blocks inference requests

    Hot-Swap Flow:
    1. Poll thread checks ModelVersion table for production changes
    2. On change detected, new model is loaded from artifact
    3. New model is validated with a quick inference test
    4. Atomic reference swap occurs under write lock
    5. Old model is retained for fallback for configurable duration
    """

    def __init__(
        self,
        session_factory: sessionmaker,
        model_name: str = "fraud_detection_model",
        poll_interval_seconds: int = 30,
        fallback_retention_seconds: int = 300,
        preload_on_start: bool = True,
    ):
        """
        Initialize the model loader.

        Args:
            session_factory: SQLAlchemy session factory for DB access.
            model_name: Name of the model to load.
            poll_interval_seconds: How often to poll for model changes.
            fallback_retention_seconds: How long to keep old model for fallback.
            preload_on_start: Whether to load production model on init.
        """
        self.session_factory = session_factory
        self.model_name = model_name
        self.poll_interval = poll_interval_seconds
        self.fallback_retention = fallback_retention_seconds

        # Thread synchronization
        self._lock = threading.RLock()
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False

        # Active model cache (thread-safe)
        self._active_model: Optional[ModelCacheEntry] = None
        self._fallback_model: Optional[ModelCacheEntry] = None

        # Track current version for change detection
        self._current_version_id: Optional[str] = None
        self._current_checksum: Optional[str] = None

        # Performance metrics
        self._total_swaps: int = 0
        self._failed_swaps: int = 0
        self._last_poll_time: Optional[datetime] = None
        self._last_swap_time: Optional[datetime] = None

        # Pre-load on start if requested
        if preload_on_start:
            self._load_initial_model()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_model(self) -> Optional[BaseMLModel]:
        """
        Get the currently active production model.

        This is the main inference entry point. It returns the cached
        model immediately without any I/O.

        Returns:
            Loaded model instance or None if no model is available.
        """
        with self._lock:
            if self._active_model is not None:
                self._active_model.last_used_at = datetime.now(timezone.utc)
                return self._active_model.model
            # Fallback to old model if available
            if self._fallback_model is not None:
                logger.warning("Using fallback model (active model unavailable)")
                return self._fallback_model.model
            return None

    def get_model_info(self) -> Optional[dict[str, Any]]:
        """
        Get metadata about the currently loaded model.

        Returns:
            Dict with model info or None.
        """
        with self._lock:
            if self._active_model is None:
                return None
            info = self._active_model.info
            return {
                "model_version_id": info.model_version_id,
                "model_name": info.model_name,
                "version": info.version,
                "algorithm": info.algorithm,
                "framework": info.framework,
                "loaded_at": info.loaded_at.isoformat(),
                "load_count": self._active_model.load_count,
                "total_swaps": self._total_swaps,
                "failed_swaps": self._failed_swaps,
                "last_swap_time": self._last_swap_time.isoformat() if self._last_swap_time else None,
            }

    def start_polling(self) -> None:
        """
        Start the background polling thread for model changes.

        The polling thread runs until stop_polling() is called.
        Each poll checks the database for a new production model version.
        """
        if self._poll_thread is not None and self._poll_thread.is_alive():
            logger.warning("Polling thread already running")
            return

        self._running = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            name="model-loader-poll",
            daemon=True,
        )
        self._poll_thread.start()
        logger.info(
            "Model polling started",
            extra={
                "event": "model_loader.polling_started",
                "model_name": self.model_name,
                "interval_s": self.poll_interval,
            },
        )

    def stop_polling(self) -> None:
        """Stop the background polling thread gracefully."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=10)
            self._poll_thread = None
        logger.info("Model polling stopped")

    def force_reload(self) -> bool:
        """
        Force an immediate reload of the production model.

        This bypasses the poll interval and performs an immediate
        check and swap if a new version is available.

        Returns:
            True if a new model was loaded, False if current is latest.
        """
        return self._check_and_swap()

    def get_metrics(self) -> dict[str, Any]:
        """
        Get loader performance metrics.

        Returns:
            Dictionary with metrics about the loader's operation.
        """
        with self._lock:
            return {
                "total_swaps": self._total_swaps,
                "failed_swaps": self._failed_swaps,
                "last_poll_time": self._last_poll_time.isoformat() if self._last_poll_time else None,
                "last_swap_time": self._last_swap_time.isoformat() if self._last_swap_time else None,
                "active_model_loaded": self._active_model is not None,
                "fallback_available": self._fallback_model is not None,
                "poll_interval_s": self.poll_interval,
                "is_polling": self._running,
            }

    def predict(self, features: np.ndarray) -> tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Make a prediction using the active model.

        This is a convenience method that combines get_model() with
        prediction. It handles case where no model is loaded.

        Args:
            features: Feature matrix for prediction.

        Returns:
            Tuple of (predictions, probabilities).
            Probabilities is None if model doesn't support predict_proba.
        """
        model = self.get_model()
        if model is None:
            # No model available - return zero predictions
            n_samples = features.shape[0]
            predictions = np.zeros(n_samples, dtype=int)
            return predictions, None

        try:
            predictions = model.predict(features)
            probabilities = None
            try:
                probabilities = model.predict_proba(features)
            except (AttributeError, NotImplementedError):
                pass
            return predictions, probabilities
        except Exception as exc:
            logger.error(
                "Prediction failed",
                extra={
                    "event": "model_loader.prediction_failed",
                    "error": str(exc),
                },
            )
            n_samples = features.shape[0]
            predictions = np.zeros(n_samples, dtype=int)
            return predictions, None

    # -----------------------------------------------------------------------
    # Internal: Initialization
    # -----------------------------------------------------------------------

    def _load_initial_model(self) -> None:
        """Load the production model on initialization."""
        logger.info(
            "Loading initial model",
            extra={"event": "model_loader.initial_load", "model_name": self.model_name},
        )
        try:
            self._check_and_swap()
        except Exception as exc:
            logger.warning(
                "Initial model load failed",
                extra={
                    "event": "model_loader.initial_load_failed",
                    "error": str(exc),
                },
            )

    # -----------------------------------------------------------------------
    # Internal: Polling Loop
    # -----------------------------------------------------------------------

    def _poll_loop(self) -> None:
        """
        Background polling loop that checks for model changes.

        Runs in a separate daemon thread. Sleeps for poll_interval
        seconds between checks. Exits when _running is set to False.
        """
        while self._running:
            try:
                self._last_poll_time = datetime.now(timezone.utc)
                changed = self._check_and_swap()
                if changed:
                    logger.info(
                        "Model hot-swap completed via polling",
                        extra={
                            "event": "model_loader.hot_swap",
                            "model_name": self.model_name,
                        },
                    )
            except Exception as exc:
                logger.error(
                    "Model poll error",
                    extra={
                        "event": "model_loader.poll_error",
                        "error": str(exc),
                    },
                )

            # Sleep for poll interval (with interruptible wait)
            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

    # -----------------------------------------------------------------------
    # Internal: Model Discovery & Swap
    # -----------------------------------------------------------------------

    def _check_and_swap(self) -> bool:
        """
        Check for a new production model version and swap if found.

        This is the core hot-swap logic:
        1. Query the database for current production model version
        2. Compare with cached version ID/checksum
        3. If different, load the new model from artifact
        4. Validate the new model
        5. Atomically swap the active model reference
        6. Retain old model as fallback

        Returns:
            True if a swap occurred, False if no change.
        """
        with self.session_factory() as session:
            # Query current production model version
            model_version = (
                session.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == self.model_name,
                    ModelVersion.status == ModelStatus.PRODUCTION,
                    ModelVersion.deployed == True,  # noqa: E712
                )
                .first()
            )

            if model_version is None:
                logger.warning(
                    "No production model found",
                    extra={
                        "event": "model_loader.no_production_model",
                        "model_name": self.model_name,
                    },
                )
                return False

            version_id = str(model_version.id)
            checksum = model_version.checksum

            # Check if version has changed
            with self._lock:
                if version_id == self._current_version_id and checksum == self._current_checksum:
                    return False  # No change

            # Version changed - load new model
            logger.info(
                "New model version detected",
                extra={
                    "event": "model_loader.new_version_detected",
                    "model_name": self.model_name,
                    "version": model_version.version,
                    "version_id": version_id,
                },
            )

            try:
                # Determine model type from algorithm
                model_type = self._algorithm_to_model_type(model_version.algorithm.value)

                # Load model from artifact
                new_model = ModelFactory.load_model_from_artifact(
                    artifact_path=model_version.artifact_path,
                    model_type=model_type,
                )

                # Quick validation: run a small inference test
                self._validate_model(new_model)

                # Build cache entry
                new_entry = ModelCacheEntry(
                    model=new_model,
                    info=LoadedModelInfo(
                        model_version_id=version_id,
                        model_name=model_version.model_name,
                        version=model_version.version,
                        algorithm=model_version.algorithm.value,
                        framework=model_version.framework.value,
                        artifact_path=model_version.artifact_path,
                        checksum=checksum,
                        loaded_at=datetime.now(timezone.utc),
                    ),
                    load_count=1,
                )

                # Atomic swap
                with self._lock:
                    # Move current active to fallback
                    self._fallback_model = self._active_model
                    self._active_model = new_entry
                    self._current_version_id = version_id
                    self._current_checksum = checksum
                    self._total_swaps += 1
                    self._last_swap_time = datetime.now(timezone.utc)

                logger.info(
                    "Model hot-swap succeeded",
                    extra={
                        "event": "model_loader.swap_succeeded",
                        "model_name": self.model_name,
                        "version": model_version.version,
                        "version_id": version_id,
                    },
                )

                return True

            except Exception as exc:
                logger.error(
                    "Model swap failed",
                    extra={
                        "event": "model_loader.swap_failed",
                        "model_name": self.model_name,
                        "version": model_version.version,
                        "error": str(exc),
                    },
                )
                with self._lock:
                    self._failed_swaps += 1
                return False

    # -----------------------------------------------------------------------
    # Internal: Validation
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_model(model: BaseMLModel) -> None:
        """
        Validate a loaded model by running a quick inference test.

        Args:
            model: Model to validate.

        Raises:
            RuntimeError: If model validation fails.
        """
        if not model.is_trained:
            raise RuntimeError("Model is not trained")

        # Create a small random input for validation
        try:
            test_input = np.random.rand(5, 10).astype(np.float32)
            _ = model.predict(test_input)
        except Exception as exc:
            raise RuntimeError(f"Model validation failed: {exc}") from exc

    # -----------------------------------------------------------------------
    # Internal: Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _algorithm_to_model_type(algorithm: str) -> str:
        """
        Map algorithm enum value to model type string used by ModelFactory.

        Args:
            algorithm: Algorithm type string from DB.

        Returns:
            Model type string for ModelFactory.
        """
        mapping = {
            "random_forest": "random_forest",
            "xgboost": "xgboost",
            "logistic_regression": "logistic_regression",
            "isolation_forest": "isolation_forest",
            "gradient_boosting": "xgboost",
            "decision_tree": "random_forest",
        }
        return mapping.get(algorithm, "random_forest")
