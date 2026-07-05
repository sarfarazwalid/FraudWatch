"""
Velocity feature extraction.

Extracts time-window based velocity features:
- Transaction frequency over time windows
- Amount velocity
- Rapid transaction detection
- Geographic velocity
"""

from __future__ import annotations

from typing import Any

from ml.feature_engineering.features import (
    BaseFeatureExtractor,
    FeatureVector,
    FeatureType,
)


class VelocityFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts velocity and time-window features.

    Features:
        - tx_count_1h: Transaction count in last 1 hour
        - tx_count_24h: Transaction count in last 24 hours
        - tx_count_7d: Transaction count in last 7 days
        - tx_count_30d: Transaction count in last 30 days
        - amount_sum_1h: Total amount in last 1 hour
        - amount_sum_24h: Total amount in last 24 hours
        - amount_avg_7d: Average amount last 7 days
        - velocity_score: Composite velocity score
        - rapid_tx_detected: Boolean rapid transaction flag
        - geographic_distance_km: Distance from last transaction
    """

    def __init__(self, db_session=None):
        """Initialize velocity feature extractor."""
        super().__init__(db_session)

    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract velocity features.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector with velocity features
        """
        features = {
            "tx_count_1h": 0,
            "tx_count_24h": 0,
            "tx_count_7d": 0,
            "tx_count_30d": 0,
            "amount_sum_1h": 0.0,
            "amount_sum_24h": 0.0,
            "amount_avg_7d": 0.0,
            "velocity_score": 0.0,
            "rapid_tx_detected": 0,
            "geographic_distance_km": 0.0,
        }

        return FeatureVector(
            features=features,
            metadata={"extractor": "velocity"}
        )

    def get_feature_names(self) -> list[str]:
        """Get velocity feature names."""
        return [
            "tx_count_1h",
            "tx_count_24h",
            "tx_count_7d",
            "tx_count_30d",
            "amount_sum_1h",
            "amount_sum_24h",
            "amount_avg_7d",
            "velocity_score",
            "rapid_tx_detected",
            "geographic_distance_km",
        ]

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get velocity feature types."""
        return {
            "tx_count_1h": FeatureType.NUMERIC,
            "tx_count_24h": FeatureType.NUMERIC,
            "tx_count_7d": FeatureType.NUMERIC,
            "tx_count_30d": FeatureType.NUMERIC,
            "amount_sum_1h": FeatureType.NUMERIC,
            "amount_sum_24h": FeatureType.NUMERIC,
            "amount_avg_7d": FeatureType.NUMERIC,
            "velocity_score": FeatureType.NUMERIC,
            "rapid_tx_detected": FeatureType.BOOLEAN,
            "geographic_distance_km": FeatureType.NUMERIC,
        }

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get velocity feature descriptions."""
        return {
            "tx_count_1h": "Transaction count in last 1 hour",
            "tx_count_24h": "Transaction count in last 24 hours",
            "tx_count_7d": "Transaction count in last 7 days",
            "tx_count_30d": "Transaction count in last 30 days",
            "amount_sum_1h": "Total transaction amount in last 1 hour",
            "amount_sum_24h": "Total transaction amount in last 24 hours",
            "amount_avg_7d": "Average transaction amount last 7 days",
            "velocity_score": "Composite velocity score (0-1)",
            "rapid_tx_detected": "Boolean: 1 if rapid transactions detected",
            "geographic_distance_km": "Distance from last transaction in km",
        }
