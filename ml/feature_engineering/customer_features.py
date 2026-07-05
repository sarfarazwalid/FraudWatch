"""
Customer behavior feature extraction.

Extracts features related to customer behavior patterns:
- Transaction frequency
- Average spending
- Maximum spending
- Account age
- Historical fraud indicators
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ml.feature_engineering.features import (
    BaseFeatureExtractor,
    FeatureVector,
    FeatureType,
)


class CustomerFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts customer behavior features.

    Features:
        - customer_tx_count: Total transaction count
        - customer_tx_frequency: Transactions per day
        - avg_spending: Average transaction amount
        - max_spending: Maximum transaction amount
        - min_spending: Minimum transaction amount
        - std_spending: Standard deviation of amounts
        - customer_account_age_days: Account age in days
        - days_since_last_tx: Days since last transaction
        - customer_risk_score: Historical risk score
        - customer_fraud_history: Boolean fraud history flag
    """

    def __init__(self, db_session=None):
        """Initialize customer feature extractor."""
        super().__init__(db_session)

    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract customer behavior features.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector with customer features
        """
        # Placeholder - in production query database
        features = {
            "customer_tx_count": 0,
            "customer_tx_frequency": 0.0,
            "avg_spending": 0.0,
            "max_spending": 0.0,
            "min_spending": 0.0,
            "std_spending": 0.0,
            "customer_account_age_days": 0,
            "days_since_last_tx": 0,
            "customer_risk_score": 0.0,
            "customer_fraud_history": 0,
        }

        return FeatureVector(
            features=features,
            metadata={"extractor": "customer"}
        )

    def get_feature_names(self) -> list[str]:
        """Get customer feature names."""
        return [
            "customer_tx_count",
            "customer_tx_frequency",
            "avg_spending",
            "max_spending",
            "min_spending",
            "std_spending",
            "customer_account_age_days",
            "days_since_last_tx",
            "customer_risk_score",
            "customer_fraud_history",
        ]

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get customer feature types."""
        return {
            "customer_tx_count": FeatureType.NUMERIC,
            "customer_tx_frequency": FeatureType.NUMERIC,
            "avg_spending": FeatureType.NUMERIC,
            "max_spending": FeatureType.NUMERIC,
            "min_spending": FeatureType.NUMERIC,
            "std_spending": FeatureType.NUMERIC,
            "customer_account_age_days": FeatureType.NUMERIC,
            "days_since_last_tx": FeatureType.NUMERIC,
            "customer_risk_score": FeatureType.NUMERIC,
            "customer_fraud_history": FeatureType.BOOLEAN,
        }

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get customer feature descriptions."""
        return {
            "customer_tx_count": "Total number of transactions by customer",
            "customer_tx_frequency": "Average transactions per day",
            "avg_spending": "Average transaction amount",
            "max_spending": "Maximum transaction amount historically",
            "min_spending": "Minimum transaction amount historically",
            "std_spending": "Standard deviation of transaction amounts",
            "customer_account_age_days": "Account age in days since creation",
            "days_since_last_tx": "Days since last transaction",
            "customer_risk_score": "Historical risk score (0-1)",
            "customer_fraud_history": "Boolean: 1 if customer has fraud history",
        }
