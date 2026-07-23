"""
Fix fraud_cases schema mismatch.

This migration fixes the discrepancy between the ORM model and database schema:
- Renames case_priority to priority
- Renames case_status to status
- Renames resolution_type to resolution
- Adds missing columns: merchant_id, severity, fraud_confirmed, loss_amount, summary
- Adds missing columns to fraud_alerts: title, description, case_id, merchant_id, creator_id, resolver_id

Revision ID: 007_fix_fraud_cases_schema
Revises: 006_fix_refresh_token_model_timezone
Create Date: 2026-01-20
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "007_fix_fraud_cases_schema"
down_revision: Union[str, None] = "006_fix_refresh_token_tz"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema to match ORM models.
    """
    # ========================================
    # Fix fraud_cases table
    # ========================================

    # Rename case_priority to priority
    op.alter_column('fraud_cases', 'case_priority', new_column_name='priority')

    # Rename case_status to status
    op.alter_column('fraud_cases', 'case_status', new_column_name='status')

    # Rename resolution_type to resolution
    op.alter_column('fraud_cases', 'resolution_type', new_column_name='resolution')

    # Add missing columns to fraud_cases
    op.add_column('fraud_cases', sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('fraud_cases', sa.Column('severity', sa.String(20), nullable=False, server_default='medium'))
    op.add_column('fraud_cases', sa.Column('fraud_confirmed', sa.Boolean, nullable=True))
    op.add_column('fraud_cases', sa.Column('loss_amount', sa.Numeric(18, 2), nullable=True))
    op.add_column('fraud_cases', sa.Column('summary', sa.Text, nullable=True))

    # Add foreign key for merchant_id
    op.create_foreign_key('fk_fraud_cases_merchant_id', 'fraud_cases', 'merchants', ['merchant_id'], ['id'])

    # Add indexes for new columns
    op.create_index('ix_fraud_cases_severity', 'fraud_cases', ['severity'])
    op.create_index('ix_fraud_cases_merchant', 'fraud_cases', ['merchant_id'])

    # Drop old indexes that referenced old column names
    op.drop_index('ix_fraud_cases_status', table_name='fraud_cases')
    op.drop_index('ix_fraud_cases_priority', table_name='fraud_cases')

    # Recreate indexes with new column names
    op.create_index('ix_fraud_cases_status', 'fraud_cases', ['status'])
    op.create_index('ix_fraud_cases_priority', 'fraud_cases', ['priority'])

    print("✓ fraud_cases table updated")

    # ========================================
    # Fix fraud_alerts table
    # ========================================

    # Add missing columns to fraud_alerts
    op.add_column('fraud_alerts', sa.Column('title', sa.String(255), nullable=False, server_default='Alert'))
    op.add_column('fraud_alerts', sa.Column('description', sa.Text, nullable=True))
    op.add_column('fraud_alerts', sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('fraud_alerts', sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('fraud_alerts', sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('fraud_alerts', sa.Column('resolver_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign keys
    op.create_foreign_key('fk_fraud_alerts_merchant_id', 'fraud_alerts', 'merchants', ['merchant_id'], ['id'])
    op.create_foreign_key('fk_fraud_alerts_creator_id', 'fraud_alerts', 'users', ['creator_id'], ['id'])
    op.create_foreign_key('fk_fraud_alerts_resolver_id', 'fraud_alerts', 'users', ['resolver_id'], ['id'])

    # Add indexes
    op.create_index('ix_fraud_alerts_case', 'fraud_alerts', ['case_id'])
    op.create_index('ix_fraud_alerts_merchant', 'fraud_alerts', ['merchant_id'])

    print("✓ fraud_alerts table updated")
    print("\n✓✓✓ SCHEMA FIX COMPLETE ✓✓✓")


def downgrade() -> None:
    """
    Downgrade database schema.
    """
    # ========================================
    # Revert fraud_alerts changes
    # ========================================

    # Drop indexes
    op.drop_index('ix_fraud_alerts_merchant', table_name='fraud_alerts')
    op.drop_index('ix_fraud_alerts_case', table_name='fraud_alerts')

    # Drop foreign keys
    op.drop_constraint('fk_fraud_alerts_resolver_id', 'fraud_alerts', type_='foreignkey')
    op.drop_constraint('fk_fraud_alerts_creator_id', 'fraud_alerts', type_='foreignkey')
    op.drop_constraint('fk_fraud_alerts_merchant_id', 'fraud_alerts', type_='foreignkey')

    # Drop columns
    op.drop_column('fraud_alerts', 'resolver_id')
    op.drop_column('fraud_alerts', 'creator_id')
    op.drop_column('fraud_alerts', 'merchant_id')
    op.drop_column('fraud_alerts', 'case_id')
    op.drop_column('fraud_alerts', 'description')
    op.drop_column('fraud_alerts', 'title')

    # ========================================
    # Revert fraud_cases changes
    # ========================================

    # Drop indexes
    op.drop_index('ix_fraud_cases_merchant', table_name='fraud_cases')
    op.drop_index('ix_fraud_cases_severity', table_name='fraud_cases')
    op.drop_index('ix_fraud_cases_priority', table_name='fraud_cases')
    op.drop_index('ix_fraud_cases_status', table_name='fraud_cases')

    # Drop foreign key
    op.drop_constraint('fk_fraud_cases_merchant_id', 'fraud_cases', type_='foreignkey')

    # Drop columns
    op.drop_column('fraud_cases', 'summary')
    op.drop_column('fraud_cases', 'loss_amount')
    op.drop_column('fraud_cases', 'fraud_confirmed')
    op.drop_column('fraud_cases', 'severity')
    op.drop_column('fraud_cases', 'merchant_id')

    # Rename columns back
    op.alter_column('fraud_cases', 'resolution', new_column_name='resolution_type')
    op.alter_column('fraud_cases', 'status', new_column_name='case_status')
    op.alter_column('fraud_cases', 'priority', new_column_name='case_priority')

    # Recreate old indexes
    op.create_index('ix_fraud_cases_priority', 'fraud_cases', ['case_priority'])
    op.create_index('ix_fraud_cases_status', 'fraud_cases', ['case_status'])

    print("✓ Database schema reverted to previous state")
