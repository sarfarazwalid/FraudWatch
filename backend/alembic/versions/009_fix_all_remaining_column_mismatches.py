from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "009_fix_all_remaining_column_mismatches"
down_revision: Union[str, None] = "008_fix_remaining_schema_issues"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema to match ORM models.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_cases_columns = [col['name'] for col in inspector.get_columns('fraud_cases')]

    if 'investigator_id' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('investigator_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_index('ix_fraud_cases_investigator_id', 'fraud_cases', ['investigator_id'])
        op.create_foreign_key('fk_fraud_cases_investigator_id', 'fraud_cases', 'users', ['investigator_id'], ['id'])
        print("✓ Added investigator_id column to fraud_cases")

    if 'escalation_level' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('escalation_level', sa.Integer, nullable=False, server_default='0'))
        print("✓ Added escalation_level column to fraud_cases")

    if 'opened_at' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True))
        op.create_index('ix_fraud_cases_opened_at', 'fraud_cases', ['opened_at'])
        print("✓ Added opened_at column to fraud_cases")

    if 'closed_at' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))
        print("✓ Added closed_at column to fraud_cases")

    try:
        conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'casestatus'"))
        casestatus_exists = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'casestatus'")).scalar()
    except Exception:
        casestatus_exists = False

    if casestatus_exists:
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status DROP DEFAULT")
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status TYPE casestatus USING status::text::casestatus")
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status SET DEFAULT 'new'::casestatus")

    existing_alerts_columns = [col['name'] for col in inspector.get_columns('fraud_alerts')]

    if 'rule_id' in existing_alerts_columns and 'triggered_rule_id' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'rule_id', new_column_name='triggered_rule_id')
        print("✓ Renamed fraud_alerts.rule_id to triggered_rule_id")

    if 'assigned_to' in existing_alerts_columns and 'assigned_analyst_id' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'assigned_to', new_column_name='assigned_analyst_id')
        print("✓ Renamed fraud_alerts.assigned_to to assigned_analyst_id")

    # Rename alert_score -> risk_score
    if 'alert_score' in existing_alerts_columns and 'risk_score' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'alert_score', new_column_name='risk_score')
        print("✓ Renamed fraud_alerts.alert_score to risk_score")

    # Rename resolution_notes -> resolution_summary
    if 'resolution_notes' in existing_alerts_columns and 'resolution_summary' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'resolution_notes', new_column_name='resolution_summary')
        print("✓ Renamed fraud_alerts.resolution_notes to resolution_summary")

    # Add missing columns
    if 'detection_method' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('detection_method', sa.String(50), nullable=True))
        print("✓ Added detection_method column to fraud_alerts")

    if 'generated_at' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True))
        op.create_index('ix_fraud_alerts_generated_at', 'fraud_alerts', ['generated_at'])
        print("✓ Added generated_at column to fraud_alerts")

    if 'acknowledged_at' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True))
        print("✓ Added acknowledged_at column to fraud_alerts")

    if 'false_positive' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('false_positive', sa.Boolean, nullable=True))
        print("✓ Added false_positive column to fraud_alerts")

    # Drop old columns that are no longer in the ORM model
    if 'alert_metadata' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'alert_metadata')
        print("✓ Dropped alert_metadata column from fraud_alerts")

    if 'alert_reasons' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'alert_reasons')
        print("✓ Dropped alert_reasons column from fraud_alerts")

    if 'assigned_at' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'assigned_at')
        print("✓ Dropped assigned_at column from fraud_alerts")

    # Drop old fraud_cases columns that are no longer in the ORM model
    if 'actual_loss' in existing_cases_columns:
        op.drop_column('fraud_cases', 'actual_loss')
        print("✓ Dropped actual_loss column from fraud_cases")

    if 'case_metadata' in existing_cases_columns:
        op.drop_column('fraud_cases', 'case_metadata')
        print("✓ Dropped case_metadata column from fraud_cases")

    if 'description' in existing_cases_columns:
        op.drop_column('fraud_cases', 'description')
        print("✓ Dropped description column from fraud_cases")

    if 'escalation_reason' in existing_cases_columns:
        op.drop_column('fraud_cases', 'escalation_reason')
        print("✓ Dropped escalation_reason column from fraud_cases")

    if 'estimated_loss' in existing_cases_columns:
        op.drop_column('fraud_cases', 'estimated_loss')
        print("✓ Dropped estimated_loss column from fraud_cases")

    if 'is_escalated' in existing_cases_columns:
        op.drop_column('fraud_cases', 'is_escalated')
        print("✓ Dropped is_escalated column from fraud_cases")

    if 'resolution_notes' in existing_cases_columns:
        op.drop_column('fraud_cases', 'resolution_notes')
        print("✓ Dropped resolution_notes column from fraud_cases")

    if 'resolved_at' in existing_cases_columns:
        op.drop_column('fraud_cases', 'resolved_at')
        print("✓ Dropped resolved_at column from fraud_cases")

    if 'title' in existing_cases_columns:
        op.drop_column('fraud_cases', 'title')
        print("✓ Dropped title column from fraud_cases")

    if 'assigned_at' in existing_cases_columns:
        op.drop_column('fraud_cases', 'assigned_at')
        print("✓ Dropped assigned_at column from fraud_cases")

    print("\n✓✓✓ ALL SCHEMA FIXES COMPLETE ✓✓✓")


def downgrade() -> None:
    """
    Downgrade database schema.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_cases_columns = [col['name'] for col in inspector.get_columns('fraud_cases')]
    existing_alerts_columns = [col['name'] for col in inspector.get_columns('fraud_alerts')]


    try:
        conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'case_status'"))
        case_status_exists = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'case_status'")).scalar()
    except Exception:
        case_status_exists = False

    if case_status_exists:
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status DROP DEFAULT")
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status TYPE case_status USING status::text::case_status")
        op.execute("ALTER TABLE fraud_cases ALTER COLUMN status SET DEFAULT 'new'::case_status")

    # Drop added columns
    if 'closed_at' in existing_cases_columns:
        op.drop_column('fraud_cases', 'closed_at')

    if 'opened_at' in existing_cases_columns:
        op.drop_index('ix_fraud_cases_opened_at', table_name='fraud_cases')
        op.drop_column('fraud_cases', 'opened_at')

    if 'escalation_level' in existing_cases_columns:
        op.drop_column('fraud_cases', 'escalation_level')
        print("✓ Dropped escalation_level column from fraud_cases")

    if 'investigator_id' in existing_cases_columns:
        op.drop_index('ix_fraud_cases_investigator_id', table_name='fraud_cases')
        op.drop_constraint('fk_fraud_cases_investigator_id', 'fraud_cases', type_='foreignkey')
        op.drop_column('fraud_cases', 'investigator_id')
        print("✓ Dropped investigator_id column from fraud_cases")

    # Re-add old columns
    if 'assigned_at' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True))
        print("✓ Re-added assigned_at column to fraud_cases")

    if 'title' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('title', sa.String(255), nullable=False, server_default=''))
        print("✓ Re-added title column to fraud_cases")

    if 'resolved_at' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
        print("✓ Re-added resolved_at column to fraud_cases")

    if 'resolution_notes' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('resolution_notes', sa.Text, nullable=True))
        print("✓ Re-added resolution_notes column to fraud_cases")

    if 'is_escalated' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('is_escalated', sa.Boolean, nullable=False, server_default='false'))
        print("✓ Re-added is_escalated column to fraud_cases")

    if 'estimated_loss' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('estimated_loss', sa.Numeric(18, 2), nullable=True))
        print("✓ Re-added estimated_loss column to fraud_cases")

    if 'escalation_reason' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('escalation_reason', sa.Text, nullable=True))
        print("✓ Re-added escalation_reason column to fraud_cases")

    if 'description' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('description', sa.Text, nullable=True))
        print("✓ Re-added description column to fraud_cases")

    if 'case_metadata' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('case_metadata', postgresql.JSONB, nullable=True))
        print("✓ Re-added case_metadata column to fraud_cases")

    if 'actual_loss' not in existing_cases_columns:
        op.add_column('fraud_cases', sa.Column('actual_loss', sa.Numeric(18, 2), nullable=True))
        print("✓ Re-added actual_loss column to fraud_cases")

    if 'false_positive' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'false_positive')
        print("✓ Dropped false_positive column from fraud_alerts")

    if 'acknowledged_at' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'acknowledged_at')
        print("✓ Dropped acknowledged_at column from fraud_alerts")

    if 'generated_at' in existing_alerts_columns:
        op.drop_index('ix_fraud_alerts_generated_at', table_name='fraud_alerts')
        op.drop_column('fraud_alerts', 'generated_at')
        print("✓ Dropped generated_at column from fraud_alerts")

    if 'detection_method' in existing_alerts_columns:
        op.drop_column('fraud_alerts', 'detection_method')
        print("✓ Dropped detection_method column from fraud_alerts")

    # Re-add old columns
    if 'assigned_at' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True))
        print("✓ Re-added assigned_at column to fraud_alerts")

    if 'alert_reasons' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('alert_reasons', postgresql.JSONB, nullable=False, server_default='[]'))
        print("✓ Re-added alert_reasons column to fraud_alerts")

    if 'alert_metadata' not in existing_alerts_columns:
        op.add_column('fraud_alerts', sa.Column('alert_metadata', postgresql.JSONB, nullable=True))
        print("✓ Re-added alert_metadata column to fraud_alerts")

    # Rename back
    if 'resolution_summary' in existing_alerts_columns and 'resolution_notes' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'resolution_summary', new_column_name='resolution_notes')
        print("✓ Renamed fraud_alerts.resolution_summary back to resolution_notes")

    if 'risk_score' in existing_alerts_columns and 'alert_score' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'risk_score', new_column_name='alert_score')
        print("✓ Renamed fraud_alerts.risk_score back to alert_score")

    if 'assigned_analyst_id' in existing_alerts_columns and 'assigned_to' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'assigned_analyst_id', new_column_name='assigned_to')
        print("✓ Renamed fraud_alerts.assigned_analyst_id back to assigned_to")

    if 'triggered_rule_id' in existing_alerts_columns and 'rule_id' not in existing_alerts_columns:
        op.alter_column('fraud_alerts', 'triggered_rule_id', new_column_name='rule_id')
        print("✓ Renamed fraud_alerts.triggered_rule_id back to rule_id")

    print("\n✓ Database schema reverted to previous state")
