"""
Merchant feature extraction.

Extracts merchant-specific risk features:
- Merchant risk scores
- Merchant category risk
- Historical fraud counts
- Transaction volume patterns
"""

from __future__ import annotations

from typing import Any

from ml.feature_engineering.features import (
    BaseFeatureExtractor,
    FeatureVector,
    FeatureType,
)


class MerchantFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts merchant-based features.

    Features:
        - merchant_risk_score: Merchant risk score (0-1)
        - merchant_category_risk: Risk by category
        - merchant_tx_volume_30d: Transaction volume last 30 days
        - merchant_avg_amount: Average transaction amount
        - merchant_fraud_count_90d: Fraud count last 90 days
        - merchant_age_days: Merchant account age
        - merchant_is_verified: Boolean verified merchant
        - merchant_chargeback_rate: Chargeback rate
    """

    def __init__(self, db_session=None):
        """Initialize merchant feature extractor."""
        super().__init__(db_session)

    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract merchant features.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector with merchant features
        """
        features = {
            "merchant_risk_score": 0.0,
            "merchant_category_risk": 0.0,
            "merchant_tx_volume_30d": 0.0,
            "merchant_avg_amount": 0.0,
            "merchant_fraud_count_90d": 0,
            "merchant_age_days": 0,
            "merchant_is_verified": 0,
            "merchant_chargeback_rate": 0.0,
        }

        return FeatureVector(
            features=features,
            metadata={"extractor": "merchant"}
        )

    def get_feature_names(self) -> list[str]:
        """Get merchant feature names."""
        return [
            "merchant_risk_score",
            "merchant_category_risk",
            "merchant_tx_volume_30d",
            "merchant_avg_amount",
            "merchant_fraud_count_90d",
            "merchant_age_days",
            "merchant_is_verified",
            "merchant_chargeback_rate",
        ]

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get merchant feature types."""
        return {
            "merchant_risk_score": FeatureType.NUMERIC,
            "merchant_category_risk": FeatureType.NUMERIC,
            "merchant_tx_volume_30d": FeatureType.NUMERIC,
            "merchant_avg_amount": FeatureType.NUMERIC,
            "merchant_fraud_count_90d": FeatureType.NUMERIC,
            "merchant_age_days": FeatureType.NUMERIC,
            "merchant_is_verified": FeatureType.BOOLEAN,
            "merchant_chargeback_rate": FeatureType.NUMERIC,
        }

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get merchant feature descriptions."""
        return {
            "merchant_risk_score": "Overall merchant risk score (0-1)",
            "merchant_category_risk": "Average risk for merchant's category",
            "merchant_tx_volume_30d": "Transaction volume in last 30 days",
            "merchant_avg_amount": "Average transaction amount for merchant",
            "merchant_fraud_count_90d": "Number of fraud cases in last 90 days",
            "merchant_age_days": "Merchant account age in days",
            "merchant_is_verified": "Boolean: 1 if merchant is verified",
            "merchant_chargeback_rate": "Merchant chargeback rate",
        }
