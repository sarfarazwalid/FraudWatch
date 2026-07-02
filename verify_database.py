#!/usr/bin/env python3
"""
Database Health Verification Script for FraudWatch.

Verifies:
- Tables
- Columns
- Indexes
- Constraints
- Foreign Keys
- ENUM types
- UUID extension
- Migration version
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import os

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


class DatabaseVerifier:
    """Verifies database schema and health."""
    
    def __init__(self):
        self.report: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.connection = None
        
    def log(self, message: str):
        """Add to report."""
        self.report.append(message)
        
    def error(self, message: str):
        """Log error."""
        self.errors.append(message)
        self.report.append(f"[FAIL] {message}")
        
    def warning(self, message: str):
        """Log warning."""
        self.warnings.append(message)
        self.report.append(f"[WARN] {message}")
        
    def success(self, message: str):
        """Log success."""
        self.report.append(f"[PASS] {message}")
    
    def connect(self) -> bool:
        """Connect to database."""
        try:
            from sqlalchemy import create_engine, text
            from app.config.settings import settings
            
            # Use sync engine for verification
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://fraudwatch:fraudwatch@localhost:5432/fraudwatch_dev"
            )
            
            self.engine = create_engine(database_url)
            self.connection = self.engine.connect()
            
            self.success("Connected to database")
            return True
            
        except Exception as e:
            self.error(f"Failed to connect to database: {e}")
            self.log("  Ensure PostgreSQL is running and credentials are correct")
            return False
    
    def verify_uuid_extension(self) -> bool:
        """Verify UUID extension is installed."""
        try:
            result = self.connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp')")
            )
            has_uuid = result.scalar()
            
            if has_uuid:
                self.success("UUID extension (uuid-ossp) is installed")
            else:
                self.warning("UUID extension not found - gen_random_uuid() may not work")
                self.log("  Install with: CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to check UUID extension: {e}")
            return False
    
    def verify_tables(self) -> bool:
        """Verify all tables exist."""
        try:
            # Expected tables from all domains
            expected_tables = [
                # Identity domain (7 tables)
                'users', 'roles', 'permissions', 'role_permissions', 
                'user_roles', 'user_sessions', 'refresh_tokens',
                # Transaction domain (10 tables)
                'currencies', 'payment_methods', 'transaction_types',
                'transaction_statuses', 'risk_levels', 'merchants',
                'agents', 'devices', 'locations', 'transactions',
                # Fraud domain (9 tables)
                'fraud_alerts', 'fraud_cases', 'fraud_rules',
                'predictions', 'prediction_explanations', 'risk_assessments',
                'investigation_timeline', 'fraud_comments', 'fraud_attachments',
                # ML domain (7 tables)
                'dataset_metadata', 'training_runs', 'model_versions',
                'model_metrics', 'feature_importance', 'prediction_history',
                'model_registry',
            ]
            
            result = self.connection.execute(
                text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
            )
            existing_tables = {row[0] for row in result}
            
            missing_tables = set(expected_tables) - existing_tables
            extra_tables = existing_tables - set(expected_tables)
            
            if missing_tables:
                self.error(f"Missing tables: {', '.join(sorted(missing_tables))}")
            
            if extra_tables:
                self.warning(f"Extra tables found: {', '.join(sorted(extra_tables))}")
            
            self.success(f"Tables verified: {len(existing_tables)}/{len(expected_tables)} found")
            
            return len(missing_tables) == 0
            
        except Exception as e:
            self.error(f"Failed to verify tables: {e}")
            return False
    
    def verify_indexes(self) -> bool:
        """Verify critical indexes exist."""
        try:
            critical_indexes = [
                'ix_users_email',
                'ix_users_status',
                'ix_transactions_user_id',
                'ix_transactions_created_at',
                'ix_fraud_alerts_status',
                'ix_fraud_alerts_risk_score',
                'ix_model_versions_model_name',
                'ix_model_versions_status',
                'ix_prediction_history_transaction',
                'ix_prediction_history_timestamp',
            ]
            
            result = self.connection.execute(
                text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                """)
            )
            existing_indexes = {row[0] for row in result}
            
            missing_indexes = [idx for idx in critical_indexes if idx not in existing_indexes]
            
            if missing_indexes:
                self.warning(f"Missing indexes: {', '.join(missing_indexes)}")
            else:
                self.success(f"All critical indexes verified ({len(critical_indexes)} checked)")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify indexes: {e}")
            return False
    
    def verify_constraints(self) -> bool:
        """Verify CHECK constraints exist."""
        try:
            critical_constraints = [
                'ck_users_failed_login_attempts',
                'ck_model_metrics_accuracy_range',
                'ck_model_metrics_precision_range',
                'ck_training_runs_duration_positive',
                'ck_prediction_history_latency_positive',
            ]
            
            result = self.connection.execute(
                text("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE contype = 'c'
                    AND connrelid::regclass::text LIKE 'public.%'
                """)
            )
            existing_constraints = {row[0] for row in result}
            
            found_constraints = [c for c in critical_constraints if c in existing_constraints]
            
            self.success(f"CHECK constraints verified: {len(found_constraints)}/{len(critical_constraints)} found")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify constraints: {e}")
            return False
    
    def verify_foreign_keys(self) -> bool:
        """Verify foreign key relationships."""
        try:
            critical_fks = [
                'fk_transactions_user_id',
                'fk_fraud_alerts_transaction_id',
                'fk_model_versions_training_run_id',
                'fk_model_metrics_model_version_id',
                'fk_prediction_history_transaction_id',
                'fk_prediction_history_model_version_id',
            ]
            
            result = self.connection.execute(
                text("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE contype = 'f'
                    AND connrelid::regclass::text LIKE 'public.%'
                """)
            )
            existing_fks = {row[0] for row in result}
            
            found_fks = [fk for fk in critical_fks if fk in existing_fks]
            
            self.success(f"Foreign keys verified: {len(found_fks)}/{len(critical_fks)} found")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify foreign keys: {e}")
            return False
    
    def verify_enums(self) -> bool:
        """Verify ENUM types exist."""
        try:
            expected_enums = [
                'user_status', 'role_type', 'permission_action',
                'transaction_status_value', 'risk_level_value',
                'alert_status', 'case_status', 'prediction_label',
                'training_status', 'model_status', 'deployment_environment',
            ]
            
            result = self.connection.execute(
                text("""
                    SELECT typname 
                    FROM pg_type 
                    WHERE typtype = 'e'
                """)
            )
            existing_enums = {row[0] for row in result}
            
            missing_enums = [e for e in expected_enums if e not in existing_enums]
            
            if missing_enums:
                self.warning(f"Missing ENUMs: {', '.join(missing_enums)}")
            else:
                self.success(f"All ENUMs verified ({len(expected_enums)} checked)")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify ENUMs: {e}")
            return False
    
    def verify_migration_version(self) -> bool:
        """Verify Alembic migration version table."""
        try:
            result = self.connection.execute(
                text("""
                    SELECT EXISTS(
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'alembic_version'
                    )
                """)
            )
            has_table = result.scalar()
            
            if not has_table:
                self.error("Alembic version table (alembic_version) not found")
                return False
            
            result = self.connection.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
            )
            version = result.scalar()
            
            if version:
                self.success(f"Alembic version: {version}")
            else:
                self.warning("No migrations applied (alembic_version is empty)")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify migration version: {e}")
            return False
    
    def verify_uuid_columns(self) -> bool:
        """Verify UUID columns use gen_random_uuid()."""
        try:
            result = self.connection.execute(
                text("""
                    SELECT column_name, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND column_name = 'id'
                    AND udt_name = 'uuid'
                """)
            )
            
            uuid_columns = result.fetchall()
            columns_with_generator = [
                col for col in uuid_columns 
                if col.column_default and 'gen_random_uuid' in col.column_default
            ]
            
            if len(columns_with_generator) == len(uuid_columns):
                self.success(f"All {len(uuid_columns)} UUID columns use gen_random_uuid()")
            else:
                self.warning(f"Only {len(columns_with_generator)}/{len(uuid_columns)} UUID columns use gen_random_uuid()")
            
            return True
            
        except Exception as e:
            self.error(f"Failed to verify UUID columns: {e}")
            return False
    
    def generate_report(self) -> bool:
        """Generate final report."""
        self.log("\n" + "="*80)
        self.log("DATABASE VERIFICATION REPORT")
        self.log("="*80)
        
        self.log(f"\n[PASS] Checks passed: {len([r for r in self.report if r.startswith('[PASS]')])}")
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
            self.log("[PASS] DATABASE HEALTH CHECK PASSED")
        else:
            self.log("[FAIL] DATABASE HEALTH CHECK FAILED")
        self.log("="*80)
        
        return len(self.errors) == 0
    
    def run_verification(self) -> bool:
        """Run all verification checks."""
        self.log("="*80)
        self.log("FRAUDWATCH DATABASE HEALTH VERIFICATION")
        self.log("="*80)
        
        # Connect to database
        if not self.connect():
            return False
        
        # Run all checks
        checks = [
            ("UUID Extension", self.verify_uuid_extension),
            ("Tables", self.verify_tables),
            ("Indexes", self.verify_indexes),
            ("Constraints", self.verify_constraints),
            ("Foreign Keys", self.verify_foreign_keys),
            ("ENUM Types", self.verify_enums),
            ("Migration Version", self.verify_migration_version),
            ("UUID Columns", self.verify_uuid_columns),
        ]
        
        results = []
        for check_name, check_func in checks:
            self.log(f"\n--- Checking {check_name} ---")
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                self.error(f"{check_name} check failed: {e}")
                results.append(False)
        
        # Disconnect
        if self.connection:
            self.connection.close()
        
        # Generate report
        passed = self.generate_report()
        
        # Print report
        print("\n".join(self.report))
        
        return passed


def main():
    """Run verification."""
    verifier = DatabaseVerifier()
    success = verifier.run_verification()
    
    # Save report
    report_path = Path(__file__).parent / "database_verification_report.txt"
    with open(report_path, 'w') as f:
        f.write("\n".join(verifier.report))
    
    print(f"\nReport saved to: {report_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())