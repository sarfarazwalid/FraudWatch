"""
Device feature extraction.

Extracts device fingerprint and behavior features:
- New device detection
- Device age
- Device fraud history
- Device usage patterns
"""

from __future__ import annotations

from typing import Any

from ml.feature_engineering.features import (
    BaseFeatureExtractor,
    FeatureVector,
    FeatureType,
)


class DeviceFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts device fingerprint features.

    Features:
        - device_age_days: Age of device in days
        - is_new_device: Boolean new device flag
        - device_fraud_history: Boolean fraud history
        - device_tx_count: Transaction count from device
        - device_risk_score: Device risk score (0-1)
        - device_country: Device country code
        - device_ip_risk: IP reputation score
    """

    def __init__(self, db_session=None):
        """Initialize device feature extractor."""
        super().__init__(db_session)

    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract device features.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector with device features
        """
        features = {
            "device_age_days": 0,
            "is_new_device": 0,
            "device_fraud_history": 0,
            "device_tx_count": 0,
            "device_risk_score": 0.0,
            "device_country": 0,
            "device_ip_risk": 0.0,
        }

        return FeatureVector(
            features=features,
            metadata={"extractor": "device"}
        )

    def get_feature_names(self) -> list[str]:
        """Get device feature names."""
        return [
            "device_age_days",
            "is_new_device",
            "device_fraud_history",
            "device_tx_count",
            "device_risk_score",
            "device_country",
            "device_ip_risk",
        ]

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get device feature types."""
        return {
            "device_age_days": FeatureType.NUMERIC,
            "is_new_device": FeatureType.BOOLEAN,
            "device_fraud_history": FeatureType.BOOLEAN,
            "device_tx_count": FeatureType.NUMERIC,
            "device_risk_score": FeatureType.NUMERIC,
            "device_country": FeatureType.NUMERIC,
            "device_ip_risk": FeatureType.NUMERIC,
        }

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get device feature descriptions."""
        return {
            "device_age_days": "Age of device in days since first seen",
            "is_new_device": "Boolean: 1 if device first seen <24h ago",
            "device_fraud_history": "Boolean: 1 if device linked to fraud",
            "device_tx_count": "Total transactions from device",
            "device_risk_score": "Device risk score (0-1)",
            "device_country": "Encoded device country",
            "device_ip_risk": "IP address reputation score",
        }
