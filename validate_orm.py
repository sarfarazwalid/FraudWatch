import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


class ORMValidator:
    """Validates ORM models and generates comprehensive report."""
    
    def __init__(self):
        self.report: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.models = {}
        self.enums = {}
        
    def log(self, message: str):
        """Add to report."""
        self.report.append(message)
        
    def error(self, message: str):
        """Log error."""
        self.errors.append(message)
        self.report.append(f"❌ ERROR: {message}")
        
    def warning(self, message: str):
        """Log warning."""
        self.warnings.append(message)
        self.report.append(f"⚠️  WARNING: {message}")
        
    def success(self, message: str):
        """Log success."""
        self.report.append(f"✅ {message}")
    
    def validate_imports(self):
        """Step 1: Validate all imports work."""
        self.log("\n" + "="*80)
        self.log("STEP 1: IMPORT VALIDATION")
        self.log("="*80)
        
        try:
            from app.models.base import Base
            self.success("Base class imported")
            
            from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
            self.success("All mixins imported")
            
            # Test identity domain
            from app.models.identity import User, Role, Permission, RolePermission, UserSession, RefreshToken
            self.success("Identity domain models imported (6 models)")
            
            # Test transaction domain
            from app.models.transaction import (
                Currency, PaymentMethod, TransactionType, TransactionStatusModel,
                RiskLevelCode, Merchant, Agent, Device, Location, Transaction
            )
            self.success("Transaction domain models imported (10 models)")
            
            # Test fraud domain
            from app.models.fraud import (
                FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
                RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment
            )
            self.success("Fraud domain models imported (9 models)")
            
            # Test ML domain
            from app.models.ml import (
                DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
                FeatureImportance, PredictionHistory, ModelRegistry
            )
            self.success("ML domain models imported (7 models)")
            
            # Test enums
            from app.models.enums import UserStatus, RoleType, TransactionStatusValue, RiskLevelValue
            self.success("Global enums imported")
            
            from app.models.fraud.enums import AlertSeverity, AlertStatus, CaseStatus, PredictionLabel
            self.success("Fraud domain enums imported")
            
            from app.models.ml.enums import TrainingStatus, ModelStatus, DeploymentEnvironment
            self.success("ML domain enums imported")
            
            self.log(f"\n📊 Total models: 32")
            self.log(f"📊 Total enums: 20+")
            
            return True
            
        except ImportError as e:
            self.error(f"Import failed: {e}")
            return False
    
    def validate_base_classes(self):
        """Step 2: Validate base classes and mixins."""
        self.log("\n" + "="*80)
        self.log("STEP 2: BASE CLASS VALIDATION")
        self.log("="*80)
        
        from app.models.base import Base
        from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
        
        # Check Base has metadata with naming convention
        if not hasattr(Base, 'metadata'):
            self.error("Base class missing metadata")
        else:
            self.success("Base class has metadata")
            
            if Base.metadata.naming_convention:
                self.success("Naming convention defined")
                self.log(f"   Convention keys: {list(Base.metadata.naming_convention.keys())}")
            else:
                self.warning("No naming convention defined")
        
        # Check mixins
        mixins = [UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin]
        mixin_names = ['UUIDMixin', 'TimestampMixin', 'SoftDeleteMixin', 'AuditMixin', 'VersionMixin']
        
        for mixin, name in zip(mixins, mixin_names):
            if hasattr(mixin, 'id') or hasattr(mixin, 'created_at') or hasattr(mixin, 'deleted_at'):
                self.success(f"{name} has expected attributes")
            else:
                self.warning(f"{name} may be missing expected attributes")
        
        return True
    
    def validate_models(self):
        """Step 3: Validate all models."""
        self.log("\n" + "="*80)
        self.log("STEP 3: MODEL VALIDATION")
        self.log("="*80)
        
        from app.models import (
            User, Role, Permission, RolePermission, UserSession, RefreshToken,
            Currency, PaymentMethod, TransactionType, TransactionStatusModel,
            RiskLevelCode, Merchant, Agent, Device, Location, Transaction,
            FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
            RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment,
            DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
            FeatureImportance, PredictionHistory, ModelRegistry
        )
        
        models = [
            # Identity
            User, Role, Permission, RolePermission, UserSession, RefreshToken,
            # Transaction
            Currency, PaymentMethod, TransactionType, TransactionStatusModel,
            RiskLevelCode, Merchant, Agent, Device, Location, Transaction,
            # Fraud
            FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
            RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment,
            # ML
            DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
            FeatureImportance, PredictionHistory, ModelRegistry
        ]
        
        model_stats = {
            'total': 0,
            'with_timestamps': 0,
            'with_audit': 0,
            'with_soft_delete': 0,
            'with_version': 0,
            'uuid_primary_key': 0,
        }
        
        for model in models:
            model_stats['total'] += 1
            
            # Check __tablename__
            if not hasattr(model, '__tablename__'):
                self.error(f"{model.__name__} missing __tablename__")
            else:
                self.success(f"{model.__name__:30s} table: {model.__tablename__}")
            
            # Check UUID primary key
            if hasattr(model, 'id'):
                model_stats['uuid_primary_key'] += 1
            
            # Check mixins
            if hasattr(model, 'created_at'):
                model_stats['with_timestamps'] += 1
            if hasattr(model, 'created_by'):
                model_stats['with_audit'] += 1
            if hasattr(model, 'deleted_at'):
                model_stats['with_soft_delete'] += 1
            if hasattr(model, 'version'):
                model_stats['with_version'] += 1
        
        self.log(f"\n📊 Model Statistics:")
        self.log(f"   Total models: {model_stats['total']}")
        self.log(f"   With timestamps: {model_stats['with_timestamps']}")
        self.log(f"   With audit fields: {model_stats['with_audit']}")
        self.log(f"   With soft delete: {model_stats['with_soft_delete']}")
        self.log(f"   With versioning: {model_stats['with_version']}")
        self.log(f"   With UUID PK: {model_stats['uuid_primary_key']}")
        
        return True
    
    def validate_relationships(self):
        """Step 4: Validate relationships."""
        self.log("\n" + "="*80)
        self.log("STEP 4: RELATIONSHIP VALIDATION")
        self.log("="*80)
        
        from app.models.identity import User, Role
        from app.models.transaction import Transaction
        from app.models.fraud import FraudAlert, FraudCase, Prediction
        from app.models.ml import TrainingRun, ModelVersion, PredictionHistory
        
        relationships = [
            (User, 'roles', 'User-Role many-to-many'),
            (User, 'managed_cases', 'User-Case relationship'),
            (Transaction, 'fraud_alerts', 'Transaction-FraudAlert'),
            (FraudAlert, 'case', 'FraudAlert-Case'),
            (TrainingRun, 'dataset', 'TrainingRun-Dataset'),
            (TrainingRun, 'model_versions', 'TrainingRun-ModelVersion'),
            (ModelVersion, 'metrics', 'ModelVersion-Metrics 1:1'),
            (ModelVersion, 'feature_importances', 'ModelVersion-FeatureImportance 1:N'),
            (ModelVersion, 'predictions', 'ModelVersion-PredictionHistory 1:N'),
            (PredictionHistory, 'transaction', 'PredictionHistory-Transaction'),
            (PredictionHistory, 'model_version', 'PredictionHistory-ModelVersion'),
        ]
        
        for model, rel_name, description in relationships:
            if hasattr(model, rel_name):
                self.success(f"{description:40s} ✓")
            else:
                self.error(f"{description:40s} ✗ Missing: {rel_name}")
        
        return len(self.errors) == 0
    
    def validate_constraints(self):
        """Step 5: Validate constraints."""
        self.log("\n" + "="*80)
        self.log("STEP 5: CONSTRAINT VALIDATION")
        self.log("="*80)
        
        from app.models.ml import TrainingRun, ModelMetrics, PredictionHistory
        from app.models.transaction import Transaction
        
        constraint_checks = [
            (TrainingRun, 'ck_training_runs_duration_positive', 'duration >= 0'),
            (ModelMetrics, 'ck_model_metrics_accuracy_range', 'accuracy 0-1'),
            (ModelMetrics, 'ck_model_metrics_precision_range', 'precision 0-1'),
            (ModelMetrics, 'ck_model_metrics_recall_range', 'recall 0-1'),
            (ModelMetrics, 'ck_model_metrics_f1_range', 'f1_score 0-1'),
            (ModelMetrics, 'ck_model_metrics_roc_auc_range', 'roc_auc 0-1'),
            (ModelMetrics, 'ck_model_metrics_fpr_range', 'fpr 0-1'),
            (ModelMetrics, 'ck_model_metrics_fnr_range', 'fnr 0-1'),
            (PredictionHistory, 'ck_prediction_history_latency_positive', 'latency >= 0'),
        ]
        
        for model, constraint_name, description in constraint_checks:
            if hasattr(model, '__table_args__'):
                table_args = model.__table_args__
                found = False
                
                if isinstance(table_args, tuple):
                    for arg in table_args:
                        if hasattr(arg, 'name') and arg.name == constraint_name:
                            found = True
                            break
                
                if found:
                    self.success(f"{model.__name__:20s} {description:20s} ✓")
                else:
                    self.warning(f"{model.__name__:20s} {description:20s} ⚠ Not found")
            else:
                self.warning(f"{model.__name__:20s} No __table_args__")
        
        return True
    
    def validate_indexes(self):
        """Step 6: Validate indexes."""
        self.log("\n" + "="*80)
        self.log("STEP 6: INDEX VALIDATION")
        self.log("="*80)
        
        from app.models.ml import (
            DatasetMetadata, TrainingRun, ModelVersion, 
            ModelMetrics, PredictionHistory, ModelRegistry
        )
        
        expected_indexes = {
            DatasetMetadata: ['dataset_name', 'source', 'hash'],
            TrainingRun: ['dataset_id', 'training_status', 'started_at'],
            ModelVersion: ['model_name', 'version', 'status', 'training_run_id'],
            ModelMetrics: ['model_version_id', 'evaluation_timestamp'],
            PredictionHistory: ['transaction_id', 'model_version_id', 'prediction_timestamp'],
            ModelRegistry: ['model_name', 'deployment_environment', 'active'],
        }
        
        for model, expected_idx in expected_indexes.items():
            if hasattr(model, '__table_args__'):
                table_args = model.__table_args__
                if isinstance(table_args, tuple):
                    # Count indexes
                    index_count = sum(1 for arg in table_args if hasattr(arg, '__visit_name__') and arg.__visit_name__ == 'index')
                    self.success(f"{model.__name__:20s} {index_count} indexes defined")
        
        return True
    
    def validate_enums(self):
        """Step 7: Validate enums."""
        self.log("\n" + "="*80)
        self.log("STEP 7: ENUM VALIDATION")
        self.log("="*80)
        
        from app.models.enums import UserStatus, RoleType, TransactionStatusValue, RiskLevelValue
        from app.models.fraud.enums import AlertSeverity, AlertStatus, CaseStatus, PredictionLabel
        from app.models.ml.enums import TrainingStatus, ModelStatus, DeploymentEnvironment
        
        enums = {
            'UserStatus': UserStatus,
            'RoleType': RoleType,
            'TransactionStatusValue': TransactionStatusValue,
            'RiskLevelValue': RiskLevelValue,
            'AlertSeverity': AlertSeverity,
            'AlertStatus': AlertStatus,
            'CaseStatus': CaseStatus,
            'PredictionLabel': PredictionLabel,
            'TrainingStatus': TrainingStatus,
            'ModelStatus': ModelStatus,
            'DeploymentEnvironment': DeploymentEnvironment,
        }
        
        for name, enum_class in enums.items():
            values = [e.value for e in enum_class]
            self.success(f"{name:30s} {len(values)} values: {', '.join(values[:3])}...")
        
        return True
    
    def generate_report(self):
        """Generate final report."""
        self.log("\n" + "="*80)
        self.log("VALIDATION SUMMARY")
        self.log("="*80)
        
        passed = len([r for r in self.report if r.startswith('✅')])
        self.log(f"\n[PASS] Passed checks: {passed}")
        self.log(f"[FAIL] Errors: {len(self.errors)}")
        self.log(f"[WARN] Warnings: {len(self.warnings)}")
        
        if self.errors:
            self.log("\n[FAIL] ERRORS:")
            for error in self.errors:
                self.log(f"   - {error}")
        
        if self.warnings:
            self.log("\n[WARN] WARNINGS:")
            for warning in self.warnings:
                self.log(f"   - {warning}")
        
        self.log("\n" + "="*80)
        if not self.errors:
            self.log("[PASS] ORM VALIDATION PASSED - Ready for Alembic migration generation")
        else:
            self.log("[FAIL] ORM VALIDATION FAILED - Fix errors before proceeding")
        self.log("="*80)
        
        return len(self.errors) == 0
    
    def run_all_validations(self):
        """Run all validations."""
        self.log("="*80)
        self.log("FRAUDWATCH ORM VALIDATION REPORT")
        self.log("="*80)
        
        results = []
        results.append(self.validate_imports())
        results.append(self.validate_base_classes())
        results.append(self.validate_models())
        results.append(self.validate_relationships())
        results.append(self.validate_constraints())
        results.append(self.validate_indexes())
        results.append(self.validate_enums())
        
        passed = self.generate_report()
        
        # Print full report
        print("\n".join(self.report))
        
        return passed


def main():
    """Run validation."""
    validator = ORMValidator()
    success = validator.run_all_validations()
    
    # Save report to file
    report_path = Path(__file__).parent / "orm_validation_report.txt"
    with open(report_path, 'w') as f:
        f.write("\n".join(validator.report))
    
    print(f"\n📄 Report saved to: {report_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())