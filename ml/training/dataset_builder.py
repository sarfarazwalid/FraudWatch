from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.models.fraud.fraud_alert import FraudAlert
from app.models.fraud.prediction import Prediction
from app.models.ml.dataset_metadata import DatasetMetadata
from app.models.transaction.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from ml.feature_engineering.features import FeatureType, FeatureVector
from ml.feature_engineering.preprocessor import FeaturePreprocessor

logger = logging.getLogger(__name__)


class DatasetSplitType(Enum):
    """Dataset split strategies."""

    RANDOM = "random"
    TIME_BASED = "time_based"
    STRATIFIED = "stratified"


@dataclass
class DatasetSplit:
    """Dataset split configuration and data."""

    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series
    split_type: DatasetSplitType
    train_ratio: float
    val_ratio: float
    test_ratio: float
    split_date: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetVersion:
    """Dataset version with complete lineage."""

    dataset_name: str
    version: int
    hash: str
    storage_path: Path
    record_count: int
    feature_count: int
    fraud_count: int
    legitimate_count: int
    feature_names: list[str]
    target_column: str = "is_fraud"
    split: Optional[DatasetSplit] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class DatasetBuilder:
    def __init__(
        self,
        session_factory: sessionmaker,
        feature_preprocessor: Optional[FeaturePreprocessor] = None,
        random_seed: int = 42,
    ):
        """
        Initialize dataset builder.

        Args:
            session_factory: SQLAlchemy session factory
            feature_preprocessor: Optional pre-fitted preprocessor
            random_seed: Random seed for reproducibility
        """
        self.settings = get_settings()
        self.session_factory = session_factory
        self.feature_preprocessor = feature_preprocessor or FeaturePreprocessor()
        self.random_seed = random_seed
        self.datasets_dir = Path("ml/datasets/processed")
        self.datasets_dir.mkdir(parents=True, exist_ok=True)

    def build_dataset(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        include_features: Optional[list[str]] = None,
        exclude_features: Optional[list[str]] = None,
        balance_classes: bool = True,
        sampling_strategy: str = "auto",
    ) -> DatasetVersion:
        logger.info("Building dataset from production data")

        # Set default date range (last 90 days)
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        # Extract data
        df = self._extract_data(start_date, end_date, min_amount, max_amount)
        logger.info(f"Extracted {len(df)} records from {start_date} to {end_date}")

        # Generate labels
        df = self._generate_labels(df)
        logger.info(f"Fraud rate: {df['is_fraud'].mean():.2%}")

        # Feature engineering
        df = self._engineer_features(df, include_features, exclude_features)
        feature_names = [col for col in df.columns if col != "is_fraud"]
        logger.info(f"Generated {len(feature_names)} features")

        # Handle class imbalance
        if balance_classes:
            df = self._balance_classes(df, sampling_strategy)
            logger.info("Applied class balancing")

        # Compute dataset hash
        dataset_hash = self._compute_hash(df)

        # Save dataset
        dataset_name = f"fraud_detection_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        storage_path = self._save_dataset(df, dataset_name, dataset_hash)

        # Create dataset version
        version = DatasetVersion(
            dataset_name=dataset_name,
            version=1,
            hash=dataset_hash,
            storage_path=storage_path,
            record_count=len(df),
            feature_count=len(feature_names),
            fraud_count=int(df["is_fraud"].sum()),
            legitimate_count=int((~df["is_fraud"].astype(bool)).sum()),
            feature_names=feature_names,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "balance_applied": balance_classes,
                "sampling_strategy": sampling_strategy,
                "random_seed": self.random_seed,
            },
        )

        # Persist to database
        self._persist_metadata(version)

        logger.info(f"Dataset created: {dataset_name} v{version.version}")
        return version

    def _extract_data(
        self,
        start_date: datetime,
        end_date: datetime,
        min_amount: Optional[float],
        max_amount: Optional[float],
    ) -> pd.DataFrame:
        """
        Extract transaction and fraud data from database.

        Args:
            start_date: Start date filter
            end_date: End date filter
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter

        Returns:
            DataFrame with raw transaction data
        """
        with self.session_factory() as session:
            # Build query
            query = session.query(Transaction).filter(
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
            )

            if min_amount is not None:
                query = query.filter(Transaction.amount >= min_amount)
            if max_amount is not None:
                query = query.filter(Transaction.amount <= max_amount)

            transactions = query.all()

            # Convert to DataFrame
            records = []
            for txn in transactions:
                record = {
                    "transaction_id": str(txn.id),
                    "amount": float(txn.amount),
                    "currency": txn.currency.value if txn.currency else None,
                    "payment_method": txn.payment_method.value if txn.payment_method else None,
                    "transaction_type": txn.transaction_type.value if txn.transaction_type else None,
                    "status": txn.status.value if txn.status else None,
                    "risk_level": txn.risk_level.value if txn.risk_level else None,
                    "created_at": txn.created_at,
                    "customer_id": str(txn.customer_id) if txn.customer_id else None,
                    "merchant_id": str(txn.merchant_id) if txn.merchant_id else None,
                    "device_id": str(txn.device_id) if txn.device_id else None,
                    "location_id": str(txn.location_id) if txn.location_id else None,
                }
                records.append(record)

            df = pd.DataFrame(records)
            return df

    def _generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate fraud labels from fraud alerts and predictions.

        Args:
            df: DataFrame with transaction data

        Returns:
            DataFrame with is_fraud label column
        """
        with self.session_factory() as session:
            # Get confirmed fraud transactions
            fraud_transaction_ids = set()

            # From fraud alerts
            fraud_alerts = session.query(FraudAlert).filter(
                FraudAlert.status.in_(["confirmed", "escalated"])
            ).all()
            fraud_transaction_ids.update(str(alert.transaction_id) for alert in fraud_alerts if alert.transaction_id)

            # From predictions with high fraud probability
            high_risk_predictions = session.query(Prediction).filter(
                Prediction.fraud_probability >= 0.8,
                Prediction.created_at >= datetime.utcnow() - timedelta(days=90),
            ).all()
            fraud_transaction_ids.update(str(pred.transaction_id) for pred in high_risk_predictions if pred.transaction_id)

            # Apply labels
            df["is_fraud"] = df["transaction_id"].isin(fraud_transaction_ids).astype(int)

            return df

    def _engineer_features(
        self,
        df: pd.DataFrame,
        include_features: Optional[list[str]],
        exclude_features: Optional[list[str]],
    ) -> pd.DataFrame:
        """
        Apply feature engineering transformations.

        Args:
            df: Raw DataFrame
            include_features: Features to include
            exclude_features: Features to exclude

        Returns:
            DataFrame with engineered features
        """
        # This would integrate with the existing feature engineering pipeline
        # For now, we'll do basic transformations

        # Temporal features
        if "created_at" in df.columns:
            df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
            df["day_of_week"] = pd.to_datetime(df["created_at"]).dt.dayofweek
            df["month"] = pd.to_datetime(df["created_at"]).dt.month

        # Amount features
        if "amount" in df.columns:
            df["log_amount"] = np.log1p(df["amount"])
            df["amount_bucket"] = pd.cut(df["amount"], bins=10, labels=False)

        # Encode categorical features
        categorical_cols = ["currency", "payment_method", "transaction_type", "status", "risk_level"]
        for col in categorical_cols:
            if col in df.columns:
                df[f"{col}_encoded"] = pd.factorize(df[col])[0]

        # Filter features
        if exclude_features:
            df = df.drop(columns=[f for f in exclude_features if f in df.columns])
        if include_features:
            df = df[[f for f in include_features if f in df.columns] + ["is_fraud"]]

        # Drop non-numeric columns (except target)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if "is_fraud" not in numeric_cols:
            numeric_cols.append("is_fraud")
        df = df[numeric_cols]

        # Fill missing values
        df = df.fillna(0)

        return df

    def _balance_classes(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """
        Handle class imbalance using SMOTE or weighting.

        Args:
            df: DataFrame with imbalanced classes
            strategy: Balancing strategy

        Returns:
            Balanced DataFrame
        """
        from imblearn.over_sampling import SMOTE

        X = df.drop("is_fraud", axis=1)
        y = df["is_fraud"]

        if strategy == "auto":
            sampling_strategy = 0.5  # Target 50% fraud rate
        else:
            sampling_strategy = strategy

        smote = SMOTE(sampling_strategy=sampling_strategy, random_state=self.random_seed)
        X_resampled, y_resampled = smote.fit_resample(X, y)

        df_resampled = pd.DataFrame(X_resampled, columns=X.columns)
        df_resampled["is_fraud"] = y_resampled

        return df_resampled

    def _compute_hash(self, df: pd.DataFrame) -> str:
        """
        Compute SHA256 hash of dataset for versioning.

        Args:
            df: DataFrame to hash

        Returns:
            SHA256 hash string
        """
        # Use pandas to_csv for deterministic output
        data_string = pd.util.hash_pandas_object(df).sum()
        return hashlib.sha256(str(data_string).encode()).hexdigest()

    def _save_dataset(self, df: pd.DataFrame, name: str, hash_suffix: str) -> Path:
        """
        Save dataset to filesystem.

        Args:
            df: DataFrame to save
            name: Dataset name
            hash_suffix: Hash suffix for filename

        Returns:
            Path to saved dataset
        """
        filename = f"{name}_{hash_suffix[:8]}.parquet"
        path = self.datasets_dir / filename
        df.to_parquet(path, index=False)
        logger.info(f"Dataset saved to {path}")
        return path

    def _persist_metadata(self, version: DatasetVersion) -> DatasetMetadata:
        """
        Persist dataset metadata to database.

        Args:
            version: Dataset version to persist

        Returns:
            DatasetMetadata database record
        """
        with self.session_factory() as session:
            metadata = DatasetMetadata(
                dataset_name=version.dataset_name,
                source="transaction_fraud_join",
                record_count=version.record_count,
                feature_count=version.feature_count,
                target_column=version.target_column,
                hash=version.hash,
                storage_path=str(version.storage_path),
                description=f"Auto-generated dataset for fraud detection training",
                schema_definition=", ".join(version.feature_names),
            )
            session.add(metadata)
            session.commit()
            session.refresh(metadata)
            return metadata

    def split_dataset(
        self,
        df: pd.DataFrame,
        split_type: DatasetSplitType = DatasetSplitType.TIME_BASED,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        time_column: Optional[str] = "created_at",
    ) -> DatasetSplit:
        """
        Split dataset into train/validation/test sets.

        Args:
            df: DataFrame to split
            split_type: Type of split strategy
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
            time_column: Column to use for time-based split

        Returns:
            DatasetSplit object
        """
        np.random.seed(self.random_seed)

        if split_type == DatasetSplitType.TIME_BASED and time_column and time_column in df.columns:
            # Sort by time
            df = df.sort_values(by=time_column)
            n = len(df)
            train_end = int(n * train_ratio)
            val_end = int(n * (train_ratio + val_ratio))

            X = df.drop("is_fraud", axis=1)
            y = df["is_fraud"]

            X_train, X_val, X_test = (
                X.iloc[:train_end],
                X.iloc[train_end:val_end],
                X.iloc[val_end:],
            )
            y_train, y_val, y_test = (
                y.iloc[:train_end],
                y.iloc[train_end:val_end],
                y.iloc[val_end:],
            )

            split_date = df[time_column].iloc[train_end]

        elif split_type == DatasetSplitType.STRATIFIED:
            from sklearn.model_selection import train_test_split

            X = df.drop("is_fraud", axis=1)
            y = df["is_fraud"]

            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=(val_ratio + test_ratio), stratify=y, random_state=self.random_seed
            )

            val_size = val_ratio / (val_ratio + test_ratio)
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp, test_size=(1 - val_size), stratify=y_temp, random_state=self.random_seed
            )

            split_date = None

        else:  # RANDOM
            from sklearn.model_selection import train_test_split

            X = df.drop("is_fraud", axis=1)
            y = df["is_fraud"]

            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=(val_ratio + test_ratio), random_state=self.random_seed
            )

            val_size = val_ratio / (val_ratio + test_ratio)
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp, test_size=(1 - val_size), random_state=self.random_seed
            )

            split_date = None

        split = DatasetSplit(
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            y_val=y_val,
            y_test=y_test,
            split_type=split_type,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            split_date=split_date,
            metadata={
                "split_seed": self.random_seed,
                "train_size": len(X_train),
                "val_size": len(X_val),
                "test_size": len(X_test),
            },
        )

        logger.info(f"Dataset split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        return split

    def load_dataset(self, path: Union[str, Path]) -> pd.DataFrame:
        """
        Load dataset from filesystem.

        Args:
            path: Path to dataset file

        Returns:
            Loaded DataFrame
        """
        path = Path(path)
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        elif path.suffix == ".csv":
            return pd.read_csv(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
