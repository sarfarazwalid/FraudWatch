from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "008_fix_remaining_schema_issues"
down_revision: Union[str, None] = "007_fix_fraud_cases_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    casestatus_enum = postgresql.ENUM(
        'new', 'triaged', 'under_investigation', 'escalated',
        'awaiting_customer', 'confirmed_fraud', 'false_positive',
        'resolved', 'closed',
        name='casestatus',
        create_type=True
    )
    casestatus_enum.create(op.get_bind(), checkfirst=True)
    print("✓ Created casestatus enum type")

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('fraud_cases')]

    if 'alert_id' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_fraud_cases_alert_id', 'fraud_cases', ['alert_id'])
        op.create_foreign_key('fk_fraud_cases_alert_id', 'fraud_cases', 'fraud_alerts', ['alert_id'], ['id'])
        print("✓ Added alert_id column to fraud_cases")

    if 'merchant_id' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_fraud_cases_merchant', 'fraud_cases', ['merchant_id'])
        op.create_foreign_key('fk_fraud_cases_merchant_id', 'fraud_cases', 'merchants', ['merchant_id'], ['id'])
        print("✓ Added merchant_id column to fraud_cases")

    if 'severity' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('severity', sa.String(20), nullable=False, server_default='medium'))
        op.create_index('ix_fraud_cases_severity', 'fraud_cases', ['severity'])
        print("✓ Added severity column to fraud_cases")

    if 'fraud_confirmed' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('fraud_confirmed', sa.Boolean, nullable=True))
        print("✓ Added fraud_confirmed column to fraud_cases")

    if 'loss_amount' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('loss_amount', sa.Numeric(18, 2), nullable=True))
        print("✓ Added loss_amount column to fraud_cases")

    if 'summary' not in existing_columns:
        op.add_column('fraud_cases', sa.Column('summary', sa.Text, nullable=True))
        print("✓ Added summary column to fraud_cases")


    existing_alert_columns = [col['name'] for col in inspector.get_columns('fraud_alerts')]

    if 'alert_number' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('alert_number', sa.String(50), nullable=True))
        op.create_index('ix_fraud_alerts_alert_number', 'fraud_alerts', ['alert_number'], unique=True)
        print("✓ Added alert_number column to fraud_alerts")

    if 'title' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('title', sa.String(255), nullable=False, server_default='Alert'))
        print("✓ Added title column to fraud_alerts")

    if 'description' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('description', sa.Text, nullable=True))
        print("✓ Added description column to fraud_alerts")

    if 'case_id' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_fraud_alerts_case', 'fraud_alerts', ['case_id'])
        op.create_foreign_key('fk_fraud_alerts_case_id', 'fraud_alerts', 'fraud_cases', ['case_id'], ['id'])
        print("✓ Added case_id column to fraud_alerts")

    if 'merchant_id' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_fraud_alerts_merchant', 'fraud_alerts', ['merchant_id'])
        op.create_foreign_key('fk_fraud_alerts_merchant_id', 'fraud_alerts', 'merchants', ['merchant_id'], ['id'])
        print("✓ Added merchant_id column to fraud_alerts")

    if 'creator_id' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key('fk_fraud_alerts_creator_id', 'fraud_alerts', 'users', ['creator_id'], ['id'])
        print("✓ Added creator_id column to fraud_alerts")

    if 'resolver_id' not in existing_alert_columns:
        op.add_column('fraud_alerts', sa.Column('resolver_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key('fk_fraud_alerts_resolver_id', 'fraud_alerts', 'users', ['resolver_id'], ['id'])
        print("✓ Added resolver_id column to fraud_alerts")


    existing_registry_columns = [col['name'] for col in inspector.get_columns('model_registry')]

    if 'is_active' in existing_registry_columns and 'active' not in existing_registry_columns:
        op.alter_column('model_registry', 'is_active', new_column_name='active')
        print("✓ Renamed model_registry.is_active to active")

    print("\n✓✓✓ SCHEMA FIX COMPLETE ✓✓✓")


def downgrade() -> None:
    """
    Downgrade database schema.

    Reverts all changes made in this migration.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_registry_columns = [col['name'] for col in inspector.get_columns('model_registry')]

    if 'active' in existing_registry_columns and 'is_active' not in existing_registry_columns:
        op.alter_column('model_registry', 'active', new_column_name='is_active')
        print("✓ Renamed model_registry.active back to is_active")

    existing_alert_columns = [col['name'] for col in inspector.get_columns('fraud_alerts')]

    if 'resolver_id' in existing_alert_columns:
        op.drop_constraint('fk_fraud_alerts_resolver_id', 'fraud_alerts', type_='foreignkey')
        op.drop_column('fraud_alerts', 'resolver_id')
        print("✓ Dropped resolver_id column from fraud_alerts")

    if 'creator_id' in existing_alert_columns:
        op.drop_constraint('fk_fraud_alerts_creator_id', 'fraud_alerts', type_='foreignkey')
        op.drop_column('fraud_alerts', 'creator_id')
        print("✓ Dropped creator_id column from fraud_alerts")

    if 'merchant_id' in existing_alert_columns:
        op.drop_index('ix_fraud_alerts_merchant', table_name='fraud_alerts')
        op.drop_constraint('fk_fraud_alerts_merchant_id', 'fraud_alerts', type_='foreignkey')
        op.drop_column('fraud_alerts', 'merchant_id')
        print("✓ Dropped merchant_id column from fraud_alerts")

    if 'case_id' in existing_alert_columns:
        op.drop_index('ix_fraud_alerts_case', table_name='fraud_alerts')
        op.drop_constraint('fk_fraud_alerts_case_id', 'fraud_alerts', type_='foreignkey')
        op.drop_column('fraud_alerts', 'case_id')
        print("✓ Dropped case_id column from fraud_alerts")

    if 'description' in existing_alert_columns:
        op.drop_column('fraud_alerts', 'description')
        print("✓ Dropped description column from fraud_alerts")

    if 'title' in existing_alert_columns:
        op.drop_column('fraud_alerts', 'title')
        print("✓ Dropped title column from fraud_alerts")

    if 'alert_number' in existing_alert_columns:
        op.drop_index('ix_fraud_alerts_alert_number', table_name='fraud_alerts')
        op.drop_column('fraud_alerts', 'alert_number')
        print("✓ Dropped alert_number column from fraud_alerts")

    existing_columns = [col['name'] for col in inspector.get_columns('fraud_cases')]

    if 'summary' in existing_columns:
        op.drop_column('fraud_cases', 'summary')
        print("✓ Dropped summary column from fraud_cases")

    if 'loss_amount' in existing_columns:
        op.drop_column('fraud_cases', 'loss_amount')
        print("✓ Dropped loss_amount column from fraud_cases")

    if 'fraud_confirmed' in existing_columns:
        op.drop_column('fraud_cases', 'fraud_confirmed')
        print("✓ Dropped fraud_confirmed column from fraud_cases")

    if 'severity' in existing_columns:
        op.drop_index('ix_fraud_cases_severity', table_name='fraud_cases')
        op.drop_column('fraud_cases', 'severity')
        print("✓ Dropped severity column from fraud_cases")

    if 'merchant_id' in existing_columns:
        op.drop_index('ix_fraud_cases_merchant', table_name='fraud_cases')
        op.drop_constraint('fk_fraud_cases_merchant_id', 'fraud_cases', type_='foreignkey')
        op.drop_column('fraud_cases', 'merchant_id')
        print("✓ Dropped merchant_id column from fraud_cases")

    if 'alert_id' in existing_columns:
        op.drop_index('ix_fraud_cases_alert_id', table_name='fraud_cases')
        op.drop_constraint('fk_fraud_cases_alert_id', 'fraud_cases', type_='foreignkey')
        op.drop_column('fraud_cases', 'alert_id')
        print("✓ Dropped alert_id column from fraud_cases")

    casestatus_enum = postgresql.ENUM(
        'new', 'triaged', 'under_investigation', 'escalated',
        'awaiting_customer', 'confirmed_fraud', 'false_positive',
        'resolved', 'closed',
        name='casestatus'
    )
    casestatus_enum.drop(op.get_bind(), checkfirst=True)
    print("✓ Dropped casestatus enum type")

    print("\n✓ Database schema reverted to previous state")
