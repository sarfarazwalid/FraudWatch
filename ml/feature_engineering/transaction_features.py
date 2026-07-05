"""
Transaction-based feature extraction.

Extracts features directly from transaction data including:
- Amount features (absolute, log-transformed)
- Temporal features (hour, day of week)
- Channel features
- Payment method features
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ml.feature_engineering.features import (
    BaseFeatureExtractor,
    FeatureVector,
    FeatureType,
    FeatureCategory,
)


class TransactionFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts transaction-level features.

    Features:
        - amount: Raw transaction amount
        - amount_log: Log-transformed amount
        - amount_zscore: Z-score of amount vs user average
        - hour_of_day: Hour of transaction (0-23)
        - day_of_week: Day of week (0-6)
        - is_weekend: Boolean weekend flag
        - is_night: Boolean night transaction flag (11PM-5AM)
        - channel_encoded: Encoded transaction channel
        - payment_method_encoded: Encoded payment method
        - transaction_type_encoded: Encoded transaction type
    """

    def __init__(self, db_session=None):
        """Initialize transaction feature extractor."""
        super().__init__(db_session)

    def extract(self, transaction_id: str) -> FeatureVector:
        """
        Extract transaction features.

        Args:
            transaction_id: Transaction UUID

        Returns:
            FeatureVector with transaction features
        """
        # In production, fetch from database
        # transaction = await self._get_transaction(transaction_id)

        # Placeholder implementation
        features = {
            "amount": 0.0,
            "amount_log": 0.0,
            "amount_zscore": 0.0,
            "hour_of_day": 0,
            "day_of_week": 0,
            "is_weekend": 0,
            "is_night": 0,
            "channel_encoded": 0,
            "payment_method_encoded": 0,
            "transaction_type_encoded": 0,
        }

        return FeatureVector(
            features=features,
            metadata={"extractor": "transaction"}
        )

    def get_feature_names(self) -> list[str]:
        """Get transaction feature names."""
        return [
            "amount",
            "amount_log",
            "amount_zscore",
            "hour_of_day",
            "day_of_week",
            "is_weekend",
            "is_night",
            "channel_encoded",
            "payment_method_encoded",
            "transaction_type_encoded",
        ]

    def get_feature_types(self) -> dict[str, FeatureType]:
        """Get transaction feature types."""
        return {
            "amount": FeatureType.NUMERIC,
            "amount_log": FeatureType.NUMERIC,
            "amount_zscore": FeatureType.NUMERIC,
            "hour_of_day": FeatureType.NUMERIC,
            "day_of_week": FeatureType.NUMERIC,
            "is_weekend": FeatureType.BOOLEAN,
            "is_night": FeatureType.BOOLEAN,
            "channel_encoded": FeatureType.NUMERIC,
            "payment_method_encoded": FeatureType.NUMERIC,
            "transaction_type_encoded": FeatureType.NUMERIC,
        }

    def get_feature_descriptions(self) -> dict[str, str]:
        """Get transaction feature descriptions."""
        return {
            "amount": "Transaction amount in currency units",
            "amount_log": "Log-transformed amount (log1p)",
            "amount_zscore": "Z-score of amount vs sender's historical average",
            "hour_of_day": "Hour of transaction (0-23)",
            "day_of_week": "Day of week (0=Monday, 6=Sunday)",
            "is_weekend": "Boolean: 1 if weekend, 0 otherwise",
            "is_night": "Boolean: 1 if 11PM-5AM, 0 otherwise",
            "channel_encoded": "Encoded transaction channel (mobile, web, etc.)",
            "payment_method_encoded": "Encoded payment method (card, wallet, etc.)",
            "transaction_type_encoded": "Encoded transaction type (transfer, payment, etc.)",
        }
