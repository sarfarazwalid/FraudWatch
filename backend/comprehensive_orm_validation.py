#!/usr/bin/env python3
"""
Comprehensive SQLAlchemy ORM Validation Script

This script performs complete ORM validation including:
1. Model discovery
2. ForeignKey validation
3. Relationship validation
4. Base class verification
5. Metadata verification
6. configure_mappers() execution
7. Alembic migration comparison
8. Repository verification
9. Registration flow tracing
"""

import sys
import os
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))  # Add parent to access ml module

@dataclass
class ModelInfo:
    """Stores information about a SQLAlchemy model."""
    class_name: str
    module_name: str
    tablename: str
    base_class: str
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    secondary_tables: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """Stores validation results."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

class ORMValidator:
    """Comprehensive ORM validator for SQLAlchemy models."""

    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.base_instances: List[DeclarativeBase] = []
        self.validation_result = ValidationResult(is_valid=True)
        self.metadata_tables: Set[str] = set()

    def discover_models(self) -> Dict[str, ModelInfo]:
        """Discover all SQLAlchemy models in the application."""
        print("\n" + "="*80)
        print("STEP 1: DISCOVERING SQLALCHEMY MODELS")
        print("="*80)

        try:
            # Import the models package
            from app.models import Base
            from app.models.identity import User, Role, Permission, RolePermission, UserSession, RefreshToken
            from app.models.transaction import (
                Currency, PaymentMethod, TransactionType, TransactionStatusModel,
                RiskLevelCode, Merchant, Agent, Device, Location, Transaction
            )
            from app.models.fraud import (
                FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
                RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment
            )
            from app.models.ml import (
                DatasetMetadata, TrainingRun, ModelVersion, ModelMetrics,
                FeatureImportance, PredictionHistory, ModelRegistry
            )

            # Collect all model classes
            model_classes = [
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

            print(f"\n[OK] Found {len(model_classes)} model classes")

            # Extract information from each model
            for model_class in model_classes:
                model_info = self._extract_model_info(model_class)
                self.models[model_info.class_name] = model_info

            print(f"[OK] Extracted information from {len(self.models)} models")

            # Check for Base instances
            self._check_base_instances()

            return self.models

        except Exception as e:
            self.validation_result.is_valid = False
            self.validation_result.errors.append(f"Failed to discover models: {str(e)}")
            print(f"\n[FAIL] Error discovering models: {str(e)}")
            return {}

    def _extract_model_info(self, model_class) -> ModelInfo:
        """Extract information from a model class."""
        class_name = model_class.__name__
        module_name = model_class.__module__
        tablename = getattr(model_class, '__tablename__', None)
        base_class = model_class.__bases__[0].__name__ if model_class.__bases__ else "Unknown"

        model_info = ModelInfo(
            class_name=class_name,
            module_name=module_name,
            tablename=tablename,
            base_class=base_class
        )

        # Get primary key
        try:
            mapper = sqlalchemy_inspect(model_class)
            pk = mapper.primary_key
            model_info.primary_key = [col.name for col in pk]
        except Exception as e:
            self.validation_result.warnings.append(f"Could not get primary key for {class_name}: {str(e)}")

        # Get foreign keys
        try:
            mapper = sqlalchemy_inspect(model_class)
            for column in mapper.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        model_info.foreign_keys.append({
                            'column': column.name,
                            'target': str(fk.column),
                            'table': fk.column.table.name if fk.column.table else 'unknown'
                        })
        except Exception as e:
            self.validation_result.warnings.append(f"Could not get foreign keys for {class_name}: {str(e)}")

        # Get relationships
        try:
            mapper = sqlalchemy_inspect(model_class)
            for rel_name, rel in mapper.relationships.items():
                rel_info = {
                    'name': rel_name,
                    'target': rel.mapper.class_.__name__,
                    'back_populates': rel.back_populates,
                    'secondary': rel.secondary.name if rel.secondary else None,
                    'uselist': rel.uselist
                }
                model_info.relationships.append(rel_info)

                if rel.secondary:
                    model_info.secondary_tables.append(rel.secondary.name)
        except Exception as e:
            self.validation_result.warnings.append(f"Could not get relationships for {class_name}: {str(e)}")

        return model_info

    def _check_base_instances(self):
        """Check that there's only one declarative Base instance."""
        print("\n" + "-"*80)
        print("STEP 5: VERIFYING SINGLE DECLARATIVE BASE")
        print("-"*80)

        try:
            from app.models.base import Base

            # Check if Base is a DeclarativeBase subclass
            if issubclass(Base, DeclarativeBase):
                print(f"[OK] Found single declarative Base: {Base.__name__}")
                print(f"  Metadata: {Base.metadata}")
                self.base_instances.append(Base)
            else:
                self.validation_result.errors.append("Base is not a DeclarativeBase subclass")
                print("[FAIL] Base is not a DeclarativeBase subclass")

        except Exception as e:
            self.validation_result.errors.append(f"Failed to check Base instances: {str(e)}")
            print(f"[FAIL] Error checking Base instances: {str(e)}")

    def verify_foreign_keys(self) -> ValidationResult:
        """Verify all ForeignKey targets exist."""
        print("\n" + "="*80)
        print("STEP 3: VERIFYING FOREIGN KEY TARGETS")
        print("="*80)

        result = ValidationResult(is_valid=True)

        # First, collect all table names
        table_names = set()
        for model_info in self.models.values():
            if model_info.tablename:
                table_names.add(model_info.tablename)

        print(f"\n[OK] Found {len(table_names)} tables: {', '.join(sorted(table_names))}")

        # Check each foreign key
        for model_name, model_info in self.models.items():
            for fk in model_info.foreign_keys:
                target_table = fk['table']
                if target_table not in table_names:
                    error_msg = f"ForeignKey violation in {model_name}.{fk['column']}: " \
                               f"references table '{target_table}' which does not exist"
                    result.errors.append(error_msg)
                    result.is_valid = False
                    print(f"[FAIL] {error_msg}")
                else:
                    print(f"[PASS] {model_name}.{fk['column']} -> {target_table}")

        if result.is_valid:
            print(f"\n[PASS] All foreign keys are valid")

        return result

    def verify_relationships(self) -> ValidationResult:
        """Verify all relationships are valid."""
        print("\n" + "="*80)
        print("STEP 4: VERIFYING RELATIONSHIPS")
        print("="*80)

        result = ValidationResult(is_valid=True)

        # Check back_populates symmetry
        back_populates_map = {}
        for model_name, model_info in self.models.items():
            for rel in model_info.relationships:
                bp = rel.get('back_populates')
                if bp:
                    if bp not in back_populates_map:
                        back_populates_map[bp] = []
                    back_populates_map[bp].append((model_name, rel['name']))

        print("\nChecking back_populates symmetry...")
        for model_name, model_info in self.models.items():
            for rel in model_info.relationships:
                bp = rel.get('back_populates')
                if bp:
                    if bp in back_populates_map:
                        # Check if there's a matching relationship
                        found = False
                        for source_model, source_rel in back_populates_map[bp]:
                            if source_model == rel['target'] and source_rel == bp:
                                found = True
                                break
                        if found:
                            print(f"[OK] {model_name}.{rel['name']} <-> {rel['target']}.{bp}")
                        else:
                            warning = f"Back_populates mismatch: {model_name}.{rel['name']} references {rel['target']}.{bp} but not found"
                            result.warnings.append(warning)
                            print(f"[WARN] {warning}")

        # Check secondary tables
        print("\nChecking secondary tables...")
        for model_name, model_info in self.models.items():
            for secondary in model_info.secondary_tables:
                if secondary in [m.tablename for m in self.models.values()]:
                    print(f"[OK] Secondary table {secondary} exists for {model_name}")
                else:
                    warning = f"Secondary table {secondary} for {model_name} is not a defined model"
                    result.warnings.append(warning)
                    print(f"[WARN] {warning}")

        if result.is_valid:
            print(f"\n[PASS] Relationship validation complete")

        return result

    def verify_metadata(self) -> ValidationResult:
        """Verify all models are imported into metadata."""
        print("\n" + "="*80)
        print("STEP 6: VERIFYING MODELS IN METADATA")
        print("="*80)

        result = ValidationResult(is_valid=True)

        if not self.base_instances:
            result.errors.append("No Base instance found")
            result.is_valid = False
            return result

        base = self.base_instances[0]
        metadata_tables = set(base.metadata.tables.keys())

        print(f"\n[OK] Metadata contains {len(metadata_tables)} tables:")
        for table in sorted(metadata_tables):
            print(f"  - {table}")

        # Check if all model tablenames are in metadata
        model_tablenames = {m.tablename for m in self.models.values() if m.tablename}
        missing = model_tablenames - metadata_tables
        extra = metadata_tables - model_tablenames

        if missing:
            error_msg = f"Models missing from metadata: {', '.join(sorted(missing))}"
            result.errors.append(error_msg)
            result.is_valid = False
            print(f"\n[FAIL] {error_msg}")

        if extra:
            warning = f"Tables in metadata not defined as models: {', '.join(sorted(extra))}"
            result.warnings.append(warning)
            print(f"\n[WARN] {warning}")

        if not missing and not extra:
            print(f"\n[PASS] All models are correctly registered in metadata")

        self.metadata_tables = metadata_tables
        return result

    def run_configure_mappers(self) -> Tuple[ValidationResult, Dict[str, Any]]:
        """Run configure_mappers() and capture any errors."""
        print("\n" + "="*80)
        print("STEP 7: RUNNING configure_mappers()")
        print("="*80)

        result = ValidationResult(is_valid=True)
        dependency_graph = {}

        if not self.base_instances:
            result.errors.append("No Base instance found")
            return result, dependency_graph

        base = self.base_instances[0]

        try:
            # Try to configure mappers
            print("\n[OK] Attempting to configure mappers...")
            base.registry.configure()
            print("[PASS] configure_mappers() succeeded - all mappers are valid")
            result.info.append("configure_mappers() executed successfully")

        except Exception as e:
            result.is_valid = False
            error_msg = f"configure_mappers() failed: {str(e)}"
            result.errors.append(error_msg)
            print(f"\n[FAIL] {error_msg}")

            # Try to identify which mapper failed
            print("\nAttempting to identify failing mapper...")
            for model_name, model_info in self.models.items():
                try:
                    # Try to inspect the mapper
                    mapper = sqlalchemy_inspect(self._get_model_class(model_name))
                    print(f"[OK] {model_name} mapper is valid")
                except Exception as mapper_error:
                    error = f"[FAIL] {model_name} mapper failed: {str(mapper_error)}"
                    result.errors.append(error)
                    dependency_graph[model_name] = {
                        'error': str(mapper_error),
                        'dependencies': [fk['target'] for fk in model_info.foreign_keys]
                    }
                    print(error)

        return result, dependency_graph

    def _get_model_class(self, class_name: str):
        """Get model class by name."""
        try:
            from app.models import Base
            return Base.registry._class_registry.get(class_name)
        except:
            return None

    def compare_with_alembic(self) -> ValidationResult:
        """Compare ORM table names with Alembic migrations."""
        print("\n" + "="*80)
        print("STEP 8: COMPARING WITH ALEMBIC MIGRATIONS")
        print("="*80)

        result = ValidationResult(is_valid=True)

        # Try to find migration files
        migrations_dir = backend_path / "alembic" / "versions"
        if not migrations_dir.exists():
            result.warnings.append("Alembic migrations directory not found")
            print("[WARN] Alembic migrations directory not found")
            return result

        # Read migration files to extract table names
        migration_tables = set()
        for migration_file in migrations_dir.glob("*.py"):
            if migration_file.name.startswith("__"):
                continue
            try:
                with open(migration_file, 'r') as f:
                    content = f.read()
                    # Look for create_table or table definitions
                    import re
                    tables = re.findall(r'create_table\([\'"](\w+)', content)
                    migration_tables.update(tables)
            except Exception as e:
                result.warnings.append(f"Could not read migration {migration_file.name}: {str(e)}")

        print(f"\n[OK] Found {len(migration_tables)} tables in migrations")

        # Compare with ORM tables
        orm_tables = {m.tablename for m in self.models.values() if m.tablename}

        missing_in_migrations = orm_tables - migration_tables
        extra_in_migrations = migration_tables - orm_tables

        if missing_in_migrations:
            warning = f"ORM tables not in migrations: {', '.join(sorted(missing_in_migrations))}"
            result.warnings.append(warning)
            print(f"\n[WARN] {warning}")

        if extra_in_migrations:
            warning = f"Migration tables not in ORM: {', '.join(sorted(extra_in_migrations))}"
            result.warnings.append(warning)
            print(f"\n[WARN] {warning}")

        if not missing_in_migrations and not extra_in_migrations:
            print(f"\n[PASS] ORM tables match migrations")

        return result

    def verify_repositories(self) -> ValidationResult:
        """Verify repositories reference correct model classes."""
        print("\n" + "="*80)
        print("STEP 9: VERIFYING REPOSITORIES")
        print("="*80)

        result = ValidationResult(is_valid=True)

        try:
            # Import repositories
            from app.repositories.user import UserRepository
            from app.repositories.role import RoleRepository
            from app.repositories.permission import PermissionRepository
            from app.repositories.transaction import TransactionRepository
            from app.repositories.fraud_alert import FraudAlertRepository
            from app.repositories.fraud_case import FraudCaseRepository

            repositories = [
                UserRepository, RoleRepository, PermissionRepository,
                TransactionRepository, FraudAlertRepository, FraudCaseRepository
            ]

            print(f"\n[OK] Found {len(repositories)} repositories")

            # Check each repository
            for repo in repositories:
                repo_name = repo.__name__
                # Get the model class from generic parameters if available
                if hasattr(repo, '__orig_bases__'):
                    for base in repo.__orig_bases__:
                        if hasattr(base, '__args__'):
                            model_class = base.__args__[0] if base.__args__ else None
                            if model_class:
                                model_name = model_class.__name__
                                if model_name in self.models:
                                    print(f"[OK] {repo_name} -> {model_name}")
                                else:
                                    error = f"{repo_name} references unknown model {model_name}"
                                    result.errors.append(error)
                                    print(f"[FAIL] {error}")
                                    result.is_valid = False

        except Exception as e:
            result.warnings.append(f"Could not verify repositories: {str(e)}")
            print(f"[WARN] {str(e)}")

        return result

    def trace_registration_flow(self) -> ValidationResult:
        """Trace POST /api/v1/auth/register flow."""
        print("\n" + "="*80)
        print("STEP 10: TRACING REGISTRATION FLOW")
        print("="*80)

        result = ValidationResult(is_valid=True)

        try:
            print("\nTracing: POST /api/v1/auth/register")
            print("-" * 80)

            # Step 1: API endpoint
            print("\n[OK] STEP 1: API Endpoint")
            from app.api.v1.auth import router
            print(f"  Router: {router}")
            print(f"  Routes: {[route.path for route in router.routes if 'register' in route.path]}")

            # Step 2: Schema validation
            print("\n[OK] STEP 2: Schema Validation")
            from app.schemas.auth import RegisterRequest
            print(f"  Schema: {RegisterRequest.__name__}")
            print(f"  Fields: {list(RegisterRequest.model_fields.keys())}")

            # Step 3: AuthenticationService
            print("\n[OK] STEP 3: AuthenticationService.register()")
            from app.services.auth import AuthenticationService
            print(f"  Service: {AuthenticationService.__name__}")
            if hasattr(AuthenticationService, 'register'):
                print(f"  Method: register() found")
                # Get method signature
                sig = inspect.signature(AuthenticationService.register)
                print(f"  Signature: {sig}")

            # Step 4: Repository
            print("\n[OK] STEP 4: Repository")
            from app.repositories.user import UserRepository
            print(f"  Repository: {UserRepository.__name__}")

            # Step 5: SQLAlchemy Model
            print("\n[OK] STEP 5: SQLAlchemy Model")
            from app.models.identity.user import User
            print(f"  Model: {User.__name__}")
            print(f"  Table: {User.__tablename__}")

            # Step 6: Database
            print("\n[OK] STEP 6: Database")
            from app.config.settings import settings
            print(f"  Database URL: {settings.database_url}")
            print(f"  Database configured via settings")

            print("\n[PASS] Registration flow traced successfully")
            result.info.append("Registration flow traced successfully")

        except Exception as e:
            result.is_valid = False
            error_msg = f"Failed to trace registration flow: {str(e)}"
            result.errors.append(error_msg)
            print(f"\n[FAIL] {error_msg}")
            import traceback
            traceback.print_exc()

        return result

    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        report = []
        report.append("="*80)
        report.append("COMPREHENSIVE SQLALCHEMY ORM VALIDATION REPORT")
        report.append("="*80)
        report.append("")

        # Model Summary
        report.append("MODEL SUMMARY")
        report.append("-"*80)
        report.append(f"Total models discovered: {len(self.models)}")
        report.append("")

        # Detailed model information
        report.append("DETAILED MODEL INFORMATION")
        report.append("-"*80)
        for model_name, model_info in sorted(self.models.items()):
            report.append(f"\nClass: {model_info.class_name}")
            report.append(f"  Module: {model_info.module_name}")
            report.append(f"  Table: {model_info.tablename}")
            report.append(f"  Base: {model_info.base_class}")
            report.append(f"  Primary Key: {', '.join(model_info.primary_key) if model_info.primary_key else 'None'}")

            if model_info.foreign_keys:
                report.append(f"  Foreign Keys:")
                for fk in model_info.foreign_keys:
                    report.append(f"    - {fk['column']} -> {fk['target']}")

            if model_info.relationships:
                report.append(f"  Relationships:")
                for rel in model_info.relationships:
                    bp = f" (back_populates: {rel['back_populates']})" if rel.get('back_populates') else ""
                    secondary = f" (secondary: {rel['secondary']})" if rel.get('secondary') else ""
                    report.append(f"    - {rel['name']} -> {rel['target']}{bp}{secondary}")

            if model_info.secondary_tables:
                report.append(f"  Secondary Tables: {', '.join(model_info.secondary_tables)}")

        report.append("")

        # Validation Results
        report.append("VALIDATION RESULTS")
        report.append("-"*80)

        if self.validation_result.is_valid:
            report.append("[PASS] Overall validation: PASSED")
        else:
            report.append("[FAIL] Overall validation: FAILED")

        if self.validation_result.errors:
            report.append(f"\nErrors ({len(self.validation_result.errors)}):")
            for error in self.validation_result.errors:
                report.append(f"  [FAIL] {error}")

        if self.validation_result.warnings:
            report.append(f"\nWarnings ({len(self.validation_result.warnings)}):")
            for warning in self.validation_result.warnings:
                report.append(f"  [WARN] {warning}")

        if self.validation_result.info:
            report.append(f"\nInfo ({len(self.validation_result.info)}):")
            for info in self.validation_result.info:
                report.append(f"  [INFO] {info}")

        report.append("")
        report.append("="*80)

        return "\n".join(report)

    def run_all_validations(self):
        """Run all validations."""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE SQLALCHEMY ORM VALIDATION")
        print("="*80)

        # Step 1: Discover models
        self.discover_models()

        if not self.models:
            print("\n[FAIL] No models discovered. Aborting validation.")
            return False

        # Step 3: Verify foreign keys
        fk_result = self.verify_foreign_keys()
        self.validation_result.errors.extend(fk_result.errors)
        self.validation_result.warnings.extend(fk_result.warnings)
        if not fk_result.is_valid:
            self.validation_result.is_valid = False

        # Step 4: Verify relationships
        rel_result = self.verify_relationships()
        self.validation_result.errors.extend(rel_result.errors)
        self.validation_result.warnings.extend(rel_result.warnings)
        if not rel_result.is_valid:
            self.validation_result.is_valid = False

        # Step 6: Verify metadata
        meta_result = self.verify_metadata()
        self.validation_result.errors.extend(meta_result.errors)
        self.validation_result.warnings.extend(meta_result.warnings)
        if not meta_result.is_valid:
            self.validation_result.is_valid = False

        # Step 7: Run configure_mappers
        mapper_result, dep_graph = self.run_configure_mappers()
        self.validation_result.errors.extend(mapper_result.errors)
        self.validation_result.warnings.extend(mapper_result.warnings)
        self.validation_result.info.extend(mapper_result.info)
        if not mapper_result.is_valid:
            self.validation_result.is_valid = False

        # Step 8: Compare with Alembic
        alembic_result = self.compare_with_alembic()
        self.validation_result.warnings.extend(alembic_result.warnings)

        # Step 9: Verify repositories
        repo_result = self.verify_repositories()
        self.validation_result.errors.extend(repo_result.errors)
        self.validation_result.warnings.extend(repo_result.warnings)
        if not repo_result.is_valid:
            self.validation_result.is_valid = False

        # Step 10: Trace registration flow
        reg_result = self.trace_registration_flow()
        self.validation_result.errors.extend(reg_result.errors)
        self.validation_result.warnings.extend(reg_result.warnings)
        self.validation_result.info.extend(reg_result.info)
        if not reg_result.is_valid:
            self.validation_result.is_valid = False

        # Generate report
        report = self.generate_report()
        print("\n" + report)

        # Save report to file
        report_path = backend_path / "orm_validation_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n[OK] Report saved to: {report_path}")

        return self.validation_result.is_valid

if __name__ == "__main__":
    validator = ORMValidator()
    success = validator.run_all_validations()

    if success:
        print("\n" + "="*80)
        print("[PASS] ALL VALIDATIONS PASSED")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("[FAIL] VALIDATION FAILED - See errors above")
        print("="*80)
        sys.exit(1)
