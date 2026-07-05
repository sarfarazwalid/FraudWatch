"""
Base feature engineering interfaces and data structures.

This module provides the abstract interfaces and data containers
for the feature engineering pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class FeatureType(str, Enum):
    """Type of feature for proper encoding."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    ORDINAL = "ordinal"


class FeatureCategory(str, Enum):
    """Category of feature for organization and documentation."""

    TRANSACTION = "transaction"
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    DEVICE = "device"
    VELOCITY = "velocity"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"
    HISTORICAL = "historical"


@dataclass
class FeatureVector:
    """
    Container for extracted features.

    Attributes:
        features: Dictionary of feature name to value
        feature_types: Dictionary mapping feature name to type
        metadata: Optional metadata about feature extraction
    """

    features: dict[str, Any]
    feature_types: dict[str, FeatureType] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_array(self, feature_order: list[str]) -> np.ndarray:
        """
        Convert feature vector to numpy array in specified order.

        Args:
            feature_order: Ordered list of feature names

        Returns:
            Numpy array of feature values
        """
        return np.array([self.features.get(f, 0.0) for f in feature_order])

    def get(self, feature_name: str, default: Any = None) -> Any:
        """Get feature value with optional default."""
        return self.features.get(feature_name, default)

    def get_numeric(self, feature_name: str, default: float = 0.0) -> float:
        """Get numeric feature value with type safety."""
        value = self.features.get(feature_name, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


class BaseFeatureExtractor(ABC):
    """
    Abstract base class for all feature extractors.

    All feature extractors must implement this interface to ensure
    consistency across the feature engineering pipeline.
    """

    def __init__(self, db_session=None):
        """
        Initialize feature extractor.

        Args:
            db_session: SQLAlchemy database session for historical queries
        """
        self.db_session = db_session

    @abstractmethod
    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract features for a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector containing extracted features
        """
        pass

    @abstractmethod
    def get_feature_names(self) -> list[str]:
        """
        Get list of feature names this extractor produces.

        Returns:
            List of feature names
        """
        pass

    @abstractmethod
    def get_feature_types(self) -> dict[str, FeatureType]:
        """
        Get mapping of feature names to their types.

        Returns:
            Dictionary mapping feature name to FeatureType
        """
        pass

    @abstractmethod
    def get_feature_descriptions(self) -> dict[str, str]:
        """
        Get human-readable descriptions of features.

        Returns:
            Dictionary mapping feature name to description
        """
        pass


class FeatureExtractor:
    """
    Main feature extraction orchestrator.

    Coordinates multiple feature extractors and combines their outputs
    into a unified feature vector for ML models.

    Usage:
        extractor = FeatureExtractor(db_session)
        feature_vector = extractor.extract_all(transaction_id)
        X = feature_vector.to_array(feature_order)
    """

    def __init__(self, db_session=None):
        """
        Initialize feature extractor pipeline.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

        # Initialize all feature extractors
        self.extractors: list[BaseFeatureExtractor] = [
            TransactionFeatureExtractor(db_session),
            CustomerFeatureExtractor(db_session),
            MerchantFeatureExtractor(db_session),
            DeviceFeatureExtractor(db_session),
            VelocityFeatureExtractor(db_session),
        ]

        # Build unified feature catalog
        self._feature_names: list[str] = []
        self._feature_types: dict[str, FeatureType] = {}
        self._feature_descriptions: dict[str, str] = {}

        for extractor in self.extractors:
            self._feature_names.extend(extractor.get_feature_names())
            self._feature_types.update(extractor.get_feature_types())
            self._feature_descriptions.update(extractor.get_feature_descriptions())

    def extract_all(self, transaction_id: str) -> FeatureVector:
        """
        Extract all features for a transaction.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Combined FeatureVector from all extractors
        """
        combined_features = {}

        for extractor in self.extractors:
            try:
                feature_vector = extractor.extract(transaction_id)
                combined_features.update(feature_vector.features)
            except Exception as e:
                # Log error but continue with other extractors
                # In production, use proper logging
                print(f"Warning: Feature extractor {extractor.__class__.__name__} failed: {e}")

        return FeatureVector(
            features=combined_features,
            feature_types=self._feature_types,
            metadata={"transaction_id": transaction_id}
        )

    def get_feature_names(self) -> list[str]:
        """Get ordered list of all feature names."""
        return self._feature_names.copy()

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get mapping of feature names to types."""
        return self._feature_types.copy()

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get feature descriptions."""
        return self._feature_descriptions.copy()

    def get_feature_count(self) -> int:
        """Get total number of features."""
        return len(self._feature_names)
