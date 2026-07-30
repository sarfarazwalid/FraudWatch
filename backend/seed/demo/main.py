"""
Demo data seeding main module.

This is the main entry point for generating comprehensive demo data
for the FraudWatch fraud detection platform.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, func

from seed.demo.config import config
from seed.demo.users import create_demo_users
from seed.demo.transactions import create_transactions
from seed.demo.fraud import create_fraud_data
from seed.demo.ml import create_ml_data
from seed.demo.analytics import create_analytics_data, create_dashboard_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DemoSeeder:
    """Main demo data seeder class."""

    def __init__(self, database_url: str):
        """Initialize seeder with database connection."""
        self.database_url = database_url
        self.engine = None
        self.session_factory = None

    async def setup(self):
        """Set up database connection."""
        logger.info("Setting up database connection...")

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
        )

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database connection established")

    async def cleanup(self):
        """Clean up database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.session_factory()

    async def seed_all(self, reset: bool = False) -> Dict[str, Any]:
        """
        Seed all demo data.

        Args:
            reset: If True, clear existing demo data before seeding

        Returns:
            Summary of created data
        """
        start_time = datetime.now(timezone.utc)
        logger.info("=" * 60)
        logger.info("FraudWatch Demo Data Seeding")
        logger.info("=" * 60)
        logger.info(f"Started at: {start_time.isoformat()}")

        if reset:
            logger.warning("Reset mode enabled - existing data will be cleared")
            await self.reset_demo_data()

        summary = {
            "started_at": start_time.isoformat(),
            "users": 0,
            "transactions": 0,
            "alerts": 0,
            "cases": 0,
            "ml_data": {},
            "analytics": 0,
        }

        async with await self.get_session() as session:
            try:
                # Phase 1: Create users
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 1: Creating Users and RBAC")
                logger.info("=" * 60)
                users = await create_demo_users(session)
                summary["users"] = len(users)
                await session.commit()
                logger.info(f"[OK] Created {len(users)} users")

                # Phase 2: Create transactions
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 2: Creating Transactions")
                logger.info("=" * 60)
                num_transactions = await create_transactions(session)
                summary["transactions"] = num_transactions
                await session.commit()
                logger.info(f"[OK] Created {num_transactions} transactions")

                # Phase 3: Create fraud data
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 3: Creating Fraud Alerts and Cases")
                logger.info("=" * 60)
                fraud_summary = await create_fraud_data(session)
                summary["alerts"] = fraud_summary.get("alerts", 0)
                summary["cases"] = fraud_summary.get("cases", 0)
                await session.commit()
                logger.info(f"[OK] Created {summary['alerts']} alerts")
                logger.info(f"[OK] Created {summary['cases']} cases")

                # Phase 4: Create ML data
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 4: Creating ML Models and Predictions")
                logger.info("=" * 60)
                ml_summary = await create_ml_data(session, num_transactions)
                summary["ml_data"] = ml_summary
                await session.commit()
                logger.info(f"[OK] Created {ml_summary.get('model_versions', 0)} model versions")
                logger.info(f"[OK] Created {ml_summary.get('prediction_histories', 0)} predictions")

                # Phase 5: Create analytics
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 5: Creating Analytics Data")
                logger.info("=" * 60)
                analytics_summary = await create_analytics_data(session)
                summary["analytics"] = analytics_summary.get("analytics_records", 0)
                await session.commit()
                logger.info(f"[OK] Created {summary['analytics']} analytics records")

                # Phase 6: Create dashboard metrics
                logger.info("\n" + "=" * 60)
                logger.info("PHASE 6: Creating Dashboard Metrics")
                logger.info("=" * 60)
                metrics = await create_dashboard_metrics(session)
                summary["dashboard_metrics"] = metrics
                logger.info(f"[OK] Dashboard metrics calculated")

            except Exception as e:
                logger.error(f"Error during seeding: {e}", exc_info=True)
                await session.rollback()
                raise

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        summary["completed_at"] = end_time.isoformat()
        summary["duration_seconds"] = duration

        logger.info("\n" + "=" * 60)
        logger.info("DEMO DATA SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Users: {summary['users']}")
        logger.info(f"Transactions: {summary['transactions']}")
        logger.info(f"Alerts: {summary['alerts']}")
        logger.info(f"Cases: {summary['cases']}")
        logger.info(f"Analytics Records: {summary['analytics']}")
        logger.info("\n" + "=" * 60)

        return summary

    async def reset_demo_data(self):
        """Reset demo data by deleting existing records."""
        logger.warning("Resetting demo data...")

        async with await self.get_session() as session:
            try:
                # Delete in reverse order of dependencies
                from app.models.fraud.fraud_comment import FraudComment
                from app.models.fraud.fraud_attachment import FraudAttachment
                from app.models.fraud.investigation_timeline import InvestigationTimeline
                from app.models.fraud.fraud_case import FraudCase
                from app.models.fraud.fraud_alert import FraudAlert
                from app.models.ml.prediction_history import PredictionHistory
                from app.models.ml.model_registry import ModelRegistry
                from app.models.ml.feature_importance import FeatureImportance
                from app.models.ml.model_metrics import ModelMetrics
                from app.models.ml.training_run import TrainingRun
                from app.models.ml.model_version import ModelVersion
                from app.models.transaction.transaction import Transaction
                from app.models.identity.user import User
                from app.models.identity.role_permission import RolePermission
                from app.models.identity.permission import Permission
                from app.models.identity.role import Role

                logger.info("Deleting existing data...")

                # Delete in order
                await session.execute(text("TRUNCATE TABLE fraud_comments CASCADE"))
                await session.execute(text("TRUNCATE TABLE fraud_attachments CASCADE"))
                await session.execute(text("TRUNCATE TABLE investigation_timeline CASCADE"))
                await session.execute(text("TRUNCATE TABLE fraud_cases CASCADE"))
                await session.execute(text("TRUNCATE TABLE fraud_alerts CASCADE"))
                await session.execute(text("TRUNCATE TABLE prediction_history CASCADE"))
                await session.execute(text("TRUNCATE TABLE model_registry CASCADE"))
                await session.execute(text("TRUNCATE TABLE feature_importance CASCADE"))
                await session.execute(text("TRUNCATE TABLE model_metrics CASCADE"))
                await session.execute(text("TRUNCATE TABLE training_runs CASCADE"))
                await session.execute(text("TRUNCATE TABLE model_versions CASCADE"))
                await session.execute(text("TRUNCATE TABLE transactions CASCADE"))
                await session.execute(text("TRUNCATE TABLE role_permissions CASCADE"))
                await session.execute(text("TRUNCATE TABLE permissions CASCADE"))
                await session.execute(text("TRUNCATE TABLE users CASCADE"))
                await session.execute(text("TRUNCATE TABLE roles CASCADE"))

                await session.commit()
                logger.info("[OK] Demo data reset complete")

            except Exception as e:
                logger.error(f"Error resetting data: {e}", exc_info=True)
                await session.rollback()
                raise

    async def verify_demo_data(self) -> Dict[str, int]:
        """Verify existing demo data."""
        logger.info("Verifying demo data...")

        async with await self.get_session() as session:
            from app.models.identity.user import User
            from app.models.transaction.transaction import Transaction
            from app.models.fraud.fraud_alert import FraudAlert
            from app.models.fraud.fraud_case import FraudCase

            user_count = await session.execute(select(func.count(User.id)))
            tx_count = await session.execute(select(func.count(Transaction.id)))
            alert_count = await session.execute(select(func.count(FraudAlert.id)))
            case_count = await session.execute(select(func.count(FraudCase.id)))

            counts = {
                "users": user_count.scalar_one(),
                "transactions": tx_count.scalar_one(),
                "alerts": alert_count.scalar_one(),
                "cases": case_count.scalar_one(),
            }

            logger.info("Current demo data counts:")
            for key, value in counts.items():
                logger.info(f"  {key}: {value}")

            return counts


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="FraudWatch Demo Data Seeder")
    parser.add_argument(
        "command",
        choices=["seed", "reset", "verify"],
        help="Command to execute: seed (create data), reset (clear data), verify (check counts)"
    )
    parser.add_argument(
        "--database-url",
        default="postgresql+asyncpg://fraudwatch:fraudwatch_password@localhost:5432/fraudwatch_db",
        help="Database connection URL"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing data before seeding (only for seed command)"
    )

    args = parser.parse_args()

    # Create seeder
    seeder = DemoSeeder(args.database_url)

    try:
        await seeder.setup()

        if args.command == "seed":
            seed_summary = await seeder.seed_all(reset=args.reset)
            logger.info("\n✓ Demo environment ready!")
            logger.info("\nDemo Credentials:")
            for cred in config.DEMO_USERS:
                logger.info(f"  {cred['email']} / {cred['password']} ({cred['role']})")

        elif args.command == "reset":
            await seeder.reset_demo_data()
            logger.info("\n✓ Demo data reset complete")

        elif args.command == "verify":
            counts = await seeder.verify_demo_data()
            if all(v > 0 for v in counts.values()):
                logger.info("\n✓ Demo data exists and looks good!")
            else:
                logger.warning("\n⚠ Demo data may be incomplete")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        await seeder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
