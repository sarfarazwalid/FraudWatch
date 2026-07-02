"""
Machine Learning Domain Enumerations.

Defines all enumerated types specific to the Machine Learning domain.
These enums support MLOps lifecycle management, training tracking, and model monitoring.
"""

from enum import Enum


class TrainingStatus(str, Enum):
    """Training execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STOPPED = "stopped"


class ModelStatus(str, Enum):
    """Model version lifecycle status."""
    DRAFT = "draft"
    TRAINING = "training"
    EVALUATING = "evaluating"
    STAGED = "staged"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class DeploymentEnvironment(str, Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"
    SHADOW = "shadow"
    EXPERIMENT = "experiment"


class PredictionStatus(str, Enum):
    """Prediction processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AlgorithmType(str, Enum):
    """ML algorithm types."""
    # Supervised Learning
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    NEURAL_NETWORK = "neural_network"
    DEEP_NEURAL_NETWORK = "deep_neural_network"
    CONVOLUTIONAL_NN = "convolutional_nn"
    RECURRENT_NN = "recurrent_nn"
    TRANSFORMER = "transformer"
    SUPPORT_VECTOR_MACHINE = "support_vector_machine"
    DECISION_TREE = "decision_tree"
    GRADIENT_BOOSTING = "gradient_boosting"
    
    # Unsupervised Learning
    K_MEANS = "k_means"
    DBSCAN = "dbscan"
    PCA = "pca"
    AUTOENCODER = "autoencoder"
    
    # Ensemble
    VOTING = "voting"
    STACKING = "stacking"
    BAGGING = "bagging"
    
    # Other
    CUSTOM = "custom"
    HYBRID = "hybrid"


class FrameworkType(str, Enum):
    """ML framework/library types."""
    SCIKIT_LEARN = "scikit_learn"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    HUGGINGFACE = "huggingface"
    SPARK_ML = "spark_ml"
    CUSTOM = "custom"


class DatasetSource(str, Enum):
    """Dataset source types."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    SYNTHETIC = "synthetic"
    AUGMENTED = "augmented"
    PUBLIC = "public"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    DATABASE = "database"
    API = "api"
    STREAMING = "streaming"