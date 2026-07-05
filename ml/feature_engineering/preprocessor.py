"""
Feature preprocessing pipeline.

Handles feature scaling, encoding, imputation, and transformation
for ML model input preparation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

from ml.feature_engineering.features import FeatureType


class FeaturePreprocessor:
    """
    Feature preprocessing pipeline.

    Handles:
    - Numerical feature scaling
    - Categorical feature encoding
    - Missing value imputation
    - Feature transformation
    """

    def __init__(self):
        """Initialize preprocessor."""
        self.scaler = StandardScaler()
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.feature_stats: dict[str, dict[str, float]] = {}

    def fit(self, feature_matrix: np.ndarray, feature_names: list[str], feature_types: dict[str, FeatureType]) -> FeaturePreprocessor:
        """
        Fit preprocessor on training data.

        Args:
            feature_matrix: Training feature matrix
            feature_names: List of feature names
            feature_types: Mapping of feature names to types

        Returns:
            Self for chaining
        """
        for idx, feature_name in enumerate(feature_names):
            feature_type = feature_types.get(feature_name, FeatureType.NUMERIC)
            col_idx = idx

            if feature_type == FeatureType.NUMERIC:
                # Compute statistics for imputation
                col_values = feature_matrix[:, col_idx]
                self.feature_stats[feature_name] = {
                    "mean": float(np.mean(col_values)),
                    "std": float(np.std(col_values)),
                    "min": float(np.min(col_values)),
                    "max": float(np.max(col_values)),
                    "median": float(np.median(col_values)),
                }

        # Fit scaler on numerical features
        numerical_indices = [
            idx for idx, name in enumerate(feature_names)
            if feature_types.get(name, FeatureType.NUMERIC) == FeatureType.NUMERIC
        ]

        if numerical_indices:
            numerical_data = feature_matrix[:, numerical_indices]
            self.scaler.fit(numerical_data)

        return self

    def transform(self, feature_vector: dict[str, Any], feature_names: list[str], feature_types: dict[str, FeatureType]) -> np.ndarray:
        """
        Transform features for model input.

        Args:
            feature_vector: Dictionary of feature values
            feature_names: Ordered list of feature names
            feature_types: Mapping of feature names to types

        Returns:
            Transformed feature array
        """
        # Build raw array
        raw_features = []
        for feature_name in feature_names:
            value = feature_vector.get(feature_name, 0.0)
            raw_features.append(float(value))

        raw_array = np.array(raw_features).reshape(1, -1)

        # Scale numerical features
        numerical_indices = [
            idx for idx, name in enumerate(feature_names)
            if feature_types.get(name, FeatureType.NUMERIC) == FeatureType.NUMERIC
        ]

        if numerical_indices:
            numerical_data = raw_array[:, numerical_indices]
            scaled_data = self.scaler.transform(numerical_data)
            raw_array[:, numerical_indices] = scaled_data

        return raw_array[0]

    def fit_transform(self, feature_matrix: np.ndarray, feature_names: list[str], feature_types: dict[str, FeatureType]) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            feature_matrix: Training feature matrix
            feature_names: List of feature names
            feature_types: Mapping of feature names to types

        Returns:
            Transformed feature matrix
        """
        self.fit(feature_matrix, feature_names, feature_types)

        transformed = np.zeros_like(feature_matrix)
        for i in range(feature_matrix.shape[0]):
            feature_dict = {
                name: feature_matrix[i, idx]
                for idx, name in enumerate(feature_names)
            }
            transformed[i] = self.transform(feature_dict, feature_names, feature_types)

        return transformed

    def get_feature_stats(self) -> dict[str, dict[str, float]]:
        """
        Get feature statistics computed during fit.

        Returns:
            Dictionary of feature statistics
        """
        return self.feature_stats.copy()
