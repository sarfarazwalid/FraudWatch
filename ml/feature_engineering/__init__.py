"""
Feature Engineering Module for FraudWatch.

This module extracts and transforms raw transaction data into ML-ready features
for fraud detection models.

Architecture:
- FeatureExtractor: Main interface for feature extraction
- TransactionFeatures: Amount, time, channel features
- CustomerFeatures: Customer behavior patterns
- MerchantFeatures: Merchant risk profiles
- DeviceFeatures: Device fingerprinting
- VelocityFeatures: Time-window aggregations
- Preprocessor: Scaling, encoding, imputation
"""

from ml.feature_engineering.features import FeatureExtractor, FeatureVector
from ml.feature_engineering.transaction_features import TransactionFeatureExtractor
from ml.feature_engineering.customer_features import CustomerFeatureExtractor
from ml.feature_engineering.merchant_features import MerchantFeatureExtractor
from ml.feature_engineering.device_features import DeviceFeatureExtractor
from ml.feature_engineering.velocity_features import VelocityFeatureExtractor
from ml.feature_engineering.preprocessor import FeaturePreprocessor

__all__ = [
    "FeatureExtractor",
    "FeatureVector",
    "TransactionFeatureExtractor",
    "CustomerFeatureExtractor",
    "MerchantFeatureExtractor",
    "DeviceFeatureExtractor",
    "VelocityFeatureExtractor",
    "FeaturePreprocessor",
]
