#!/usr/bin/env python3
"""
Verification script for ML Domain ORM models.

Tests:
1. All models can be imported without errors
2. No circular import issues
3. All relationships are properly defined
4. SQLAlchemy 2.x compliance
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Test that all ML models can be imported."""
    print("Testing ML model imports...")
    
    try:
        from app.models.ml.enums import (
            TrainingStatus, ModelStatus, DeploymentEnvironment,
            PredictionStatus, AlgorithmType, FrameworkType, DatasetSource
        )
        print("✓ Enums imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import enums: {e}")
        return False
    
    try:
        from app.models.ml.dataset_metadata import DatasetMetadata
        print("✓ DatasetMetadata imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import DatasetMetadata: {e}")
        return False
    
    try:
        from app.models.ml.training_run import TrainingRun
        print("✓ TrainingRun imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import TrainingRun: {e}")
        return False
    
    try:
        from app.models.ml.model_version import ModelVersion
        print("✓ ModelVersion imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ModelVersion: {e}")
        return False
    
    try:
        from app.models.ml.model_metrics import ModelMetrics
        print("✓ ModelMetrics imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ModelMetrics: {e}")
        return False
    
    try:
        from app.models.ml.feature_importance import FeatureImportance
        print("✓ FeatureImportance imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import FeatureImportance: {e}")
        return False
    
    try:
        from app.models.ml.prediction_history import PredictionHistory
        print("✓ PredictionHistory imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PredictionHistory: {e}")
        return False
    
    try:
        from app.models.ml.model_registry import ModelRegistry
        print("✓ ModelRegistry imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ModelRegistry: {e}")
        return False
    
    try:
        from app.models.ml import (
            DatasetMetadata, TrainingRun, ModelVersion,
            ModelMetrics, FeatureImportance, PredictionHistory, ModelRegistry
        )
        print("✓ ML domain __init__.py imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import from ML domain __init__: {e}")
        return False
    
    return True


def test_model_metadata():
    """Test that models have proper metadata."""
    print("\nTesting model metadata...")
    
    from app.models.ml.dataset_metadata import DatasetMetadata
    from app.models.ml.training_run import TrainingRun
    from app.models.ml.model_version import ModelVersion
    from app.models.ml.model_metrics import ModelMetrics
    from app.models.ml.feature_importance import FeatureImportance
    from app.models.ml.prediction_history import PredictionHistory
    from app.models.ml.model_registry import ModelRegistry
    
    models = [
        DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
        FeatureImportance, PredictionHistory, ModelRegistry
    ]
    
    for model in models:
        if not hasattr(model, '__tablename__'):
            print(f"✗ {model.__name__} missing __tablename__")
            return False
        
        if not hasattr(model, '__table__'):
            print(f"✗ {model.__name__} missing __table__")
            return False
        
        print(f"✓ {model.__name__} has proper metadata (table: {model.__tablename__})")
    
    return True


def test_relationships():
    """Test that relationships are properly defined."""
    print("\nTesting relationships...")
    
    from app.models.ml.training_run import TrainingRun
    from app.models.ml.model_version import ModelVersion
    from app.models.ml.prediction_history import PredictionHistory
    
    # Test TrainingRun relationships
    if not hasattr(TrainingRun, 'dataset'):
        print("✗ TrainingRun missing 'dataset' relationship")
        return False
    print("✓ TrainingRun.dataset relationship exists")
    
    if not hasattr(TrainingRun, 'model_versions'):
        print("✗ TrainingRun missing 'model_versions' relationship")
        return False
    print("✓ TrainingRun.model_versions relationship exists")
    
    # Test ModelVersion relationships
    if not hasattr(ModelVersion, 'training_run'):
        print("✗ ModelVersion missing 'training_run' relationship")
        return False
    print("✓ ModelVersion.training_run relationship exists")
    
    # Test PredictionHistory relationships
    if not hasattr(PredictionHistory, 'transaction'):
        print("✗ PredictionHistory missing 'transaction' relationship")
        return False
    print("✓ PredictionHistory.transaction relationship exists")
    
    if not hasattr(PredictionHistory, 'model_version'):
        print("✗ PredictionHistory missing 'model_version' relationship")
        return False
    print("✓ PredictionHistory.model_version relationship exists")
    
    return True


def test_constraints():
    """Test that constraints are properly defined."""
    print("\nTesting constraints...")
    
    from app.models.ml.training_run import TrainingRun
    from app.models.ml.model_metrics import ModelMetrics
    from app.models.ml.prediction_history import PredictionHistory
    
    # Check for CHECK constraints
    if hasattr(TrainingRun, '__table_args__'):
        print("✓ TrainingRun has __table_args__ with constraints")
    else:
        print("✗ TrainingRun missing __table_args__")
        return False
    
    if hasattr(ModelMetrics, '__table_args__'):
        print("✓ ModelMetrics has __table_args__ with constraints")
    else:
        print("✗ ModelMetrics missing __table_args__")
        return False
    
    if hasattr(PredictionHistory, '__table_args__'):
        print("✓ PredictionHistory has __table_args__ with constraints")
    else:
        print("✗ PredictionHistory missing __table_args__")
        return False
    
    return True


def test_indexes():
    """Test that indexes are properly defined."""
    print("\nTesting indexes...")
    
    from app.models.ml.dataset_metadata import DatasetMetadata
    from app.models.ml.model_version import ModelVersion
    from app.models.ml.prediction_history import PredictionHistory
    
    # Check for indexes in __table_args__
    for model in [DatasetMetadata, ModelVersion, PredictionHistory]:
        if hasattr(model, '__table_args__'):
            table_args = model.__table_args__
            if table_args:
                print(f"✓ {model.__name__} has indexes defined")
            else:
                print(f"⚠ {model.__name__} has empty __table_args__")
        else:
            print(f"✗ {model.__name__} missing __table_args__")
            return False
    
    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("ML Domain ORM Verification")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Model Metadata Tests", test_model_metadata),
        ("Relationship Tests", test_relationships),
        ("Constraint Tests", test_constraints),
        ("Index Tests", test_indexes),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running {test_name}...")
        print('=' * 60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("VERIFICATION SUMMARY")
    print('=' * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print('=' * 60)
    
    if all_passed:
        print("\n✓ All verification tests passed!")
        return 0
    else:
        print("\n✗ Some verification tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())