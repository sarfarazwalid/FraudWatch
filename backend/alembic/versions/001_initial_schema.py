"""
Initial schema migration for FraudWatch.

This migration creates the complete database schema including:
- 33 tables across 4 domains (Identity, Transaction, Fraud, ML)
- 31 ENUM types for domain-specific values
- CHECK constraints for data integrity
- Foreign key relationships with CASCADE/RESTRICT
- Indexes for query optimization
- UUID primary keys with gen_random_uuid()
- JSONB columns for extensible data

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-20
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection
from typing import cast

# revision identifiers
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema.

    Creates all tables, enums, constraints, and indexes in dependency order:
    1. ENUM types (no dependencies)
    2. Reference tables (currencies, etc.)
    3. Core entities (users, transactions, etc.)
    4. Dependent entities (sessions, alerts, predictions)
    """
    # ========================================
    # ENUM TYPES (31 total)
    # ========================================

    # Identity domain enums (6)
    user_status = postgresql.ENUM('active', 'inactive', 'suspended', 'locked', 'pending_verification', name='user_status')
    user_status.create(cast(op.get_bind(), Connection))

    role_type = postgresql.ENUM('super_admin', 'admin', 'fraud_analyst', 'compliance_officer', 'viewer', name='role_type')
    role_type.create(cast(op.get_bind(), Connection))

    permission_action = postgresql.ENUM('create', 'read', 'update', 'delete', 'execute', name='permission_action')
    permission_action.create(cast(op.get_bind(), Connection))

    session_status = postgresql.ENUM('active', 'expired', 'revoked', name='session_status')
    session_status.create(cast(op.get_bind(), Connection))

    token_type = postgresql.ENUM('access', 'refresh', name='token_type')
    token_type.create(cast(op.get_bind(), Connection))

    authentication_provider = postgresql.ENUM('local', 'sso', 'oauth2', name='authentication_provider')
    authentication_provider.create(cast(op.get_bind(), Connection))

    # Transaction domain enums (7)
    transaction_status_value = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'flagged', 'cancelled', 'refunded', 'reversed', name='transaction_status_value')
    transaction_status_value.create(cast(op.get_bind(), Connection))

    risk_level_value = postgresql.ENUM('low', 'medium', 'high', 'critical', name='risk_level_value')
    risk_level_value.create(cast(op.get_bind(), Connection))

    transaction_channel = postgresql.ENUM('mobile_app', 'web', 'ussd', 'api', 'pos', 'atm', 'agent', 'branch', name='transaction_channel')
    transaction_channel.create(cast(op.get_bind(), Connection))

    source_system = postgresql.ENUM('core_banking', 'switch', 'wallet', 'payment_gateway', 'bill_pay', 'third_party', 'manual', name='source_system')
    source_system.create(cast(op.get_bind(), Connection))

    currency_code = postgresql.ENUM('USD', 'EUR', 'GBP', 'KES', 'NGN', 'GHS', 'ZAR', name='currency_code')
    currency_code.create(cast(op.get_bind(), Connection))

    payment_method_type = postgresql.ENUM('card', 'bank_transfer', 'mobile_money', 'ussd', 'qr_code', name='payment_method_type')
    payment_method_type.create(cast(op.get_bind(), Connection))

    transaction_type_value = postgresql.ENUM('debit', 'credit', 'transfer', 'withdrawal', 'deposit', 'payment', 'refund', 'fee', name='transaction_type_value')
    transaction_type_value.create(cast(op.get_bind(), Connection))

    # Fraud domain enums (10)
    alert_severity = postgresql.ENUM('low', 'medium', 'high', 'critical', name='alert_severity')
    alert_severity.create(cast(op.get_bind(), Connection))

    alert_status = postgresql.ENUM('new', 'triaged', 'acknowledged', 'assigned', 'escalated', 'resolved', 'dismissed', 'false_positive', name='alert_status')
    alert_status.create(cast(op.get_bind(), Connection))

    case_priority = postgresql.ENUM('low', 'medium', 'high', 'critical', name='case_priority')
    case_priority.create(cast(op.get_bind(), Connection))

    case_status = postgresql.ENUM('new', 'triaged', 'under_investigation', 'escalated', 'awaiting_customer', 'confirmed_fraud', 'false_positive', 'resolved', 'closed', name='case_status')
    case_status.create(cast(op.get_bind(), Connection))

    detection_method = postgresql.ENUM('rule_based', 'machine_learning', 'statistical', 'behavioral', 'network', 'manual', 'hybrid', name='detection_method')
    detection_method.create(cast(op.get_bind(), Connection))

    prediction_label = postgresql.ENUM('fraud', 'legitimate', 'suspicious', 'unknown', name='prediction_label')
    prediction_label.create(cast(op.get_bind(), Connection))

    risk_decision = postgresql.ENUM('approve', 'review', 'reject', 'block', 'escalate', name='risk_decision')
    risk_decision.create(cast(op.get_bind(), Connection))

    timeline_action_type = postgresql.ENUM('created', 'status_changed', 'assigned', 'escalated', 'comment_added', 'attachment_added', 'note_added', 'customer_contacted', 'evidence_added', 'closed', 'reopened', name='timeline_action_type')
    timeline_action_type.create(cast(op.get_bind(), Connection))

    comment_visibility = postgresql.ENUM('internal', 'external', 'restricted', name='comment_visibility')
    comment_visibility.create(cast(op.get_bind(), Connection))

    attachment_type = postgresql.ENUM('document', 'image', 'video', 'audio', 'spreadsheet', 'log_file', 'screenshot', 'other', name='attachment_type')
    attachment_type.create(cast(op.get_bind(), Connection))

    explanation_method = postgresql.ENUM('shap', 'lime', 'feature_importance', 'rule_explanation', 'counterfactual', 'attention', 'other', name='explanation_method')
    explanation_method.create(cast(op.get_bind(), Connection))

    # ML domain enums (8)
    training_status = postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'stopped', name='training_status')
    training_status.create(cast(op.get_bind(), Connection))

    model_status = postgresql.ENUM('draft', 'training', 'evaluating', 'staged', 'production', 'archived', 'deprecated', 'failed', name='model_status')
    model_status.create(cast(op.get_bind(), Connection))

    deployment_environment = postgresql.ENUM('development', 'staging', 'production', 'canary', 'shadow', 'experiment', name='deployment_environment')
    deployment_environment.create(cast(op.get_bind(), Connection))

    prediction_status_enum = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'timeout', name='prediction_status')
    prediction_status_enum.create(cast(op.get_bind(), Connection))

    algorithm_type = postgresql.ENUM('logistic_regression', 'random_forest', 'xgboost', 'lightgbm', 'catboost', 'neural_network', 'deep_neural_network', 'convolutional_nn', 'recurrent_nn', 'transformer', 'support_vector_machine', 'decision_tree', 'gradient_boosting', 'k_means', 'dbscan', 'pca', 'autoencoder', 'voting', 'stacking', 'bagging', 'custom', 'hybrid', name='algorithm_type')
    algorithm_type.create(cast(op.get_bind(), Connection))

    framework_type = postgresql.ENUM('scikit_learn', 'tensorflow', 'pytorch', 'xgboost', 'lightgbm', 'catboost', 'huggingface', 'spark_ml', 'custom', name='framework_type')
    framework_type.create(cast(op.get_bind(), Connection))

    dataset_source = postgresql.ENUM('internal', 'external', 'synthetic', 'augmented', 'public', 's3', 'gcs', 'azure_blob', 'database', 'api', 'streaming', name='dataset_source')
    dataset_source.create(cast(op.get_bind(), Connection))

    print("✓ Created 31 ENUM types")

    # ========================================
    # IDENTITY DOMAIN (7 tables)
    # ========================================

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('status', user_status, nullable=False, server_default='pending_verification'),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('phone_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('authentication_provider', authentication_provider, nullable=False, server_default='local'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(1024), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_users_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_users_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.UniqueConstraint('external_id', name='uq_users_external_id'),
        sa.CheckConstraint('failed_login_attempts >= 0', name='ck_users_failed_login_attempts'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

    # Roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('role_type', role_type, nullable=False, server_default='viewer'),
        sa.Column('is_system_role', sa.Boolean, nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_roles_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_roles_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_roles'),
        sa.UniqueConstraint('name', name='uq_roles_name'),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', permission_action, nullable=False),
        sa.Column('conditions', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_permissions_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_permissions_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_permissions'),
        sa.UniqueConstraint('resource', 'action', name='uq_permissions_resource_action'),
    )
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_index('ix_permissions_action', 'permissions', ['action'])

    # Role-Permission association table
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_role_permissions_role_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], name='fk_role_permissions_permission_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_role_permissions'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions_role_permission'),
    )
    op.create_index('ix_role_permissions_role', 'role_permissions', ['role_id'])
    op.create_index('ix_role_permissions_permission', 'role_permissions', ['permission_id'])

    # User-Role association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_roles_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_user_roles_role_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], name='fk_user_roles_assigned_by'),
        sa.PrimaryKeyConstraint('user_id', 'role_id', name='pk_user_roles'),
    )
    op.create_index('ix_user_roles_user', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role', 'user_roles', ['role_id'])

    # User sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_jti', sa.String(255), nullable=False),
        sa.Column('status', session_status, nullable=False, server_default='active'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_sessions_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_user_sessions_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_user_sessions_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_user_sessions'),
        sa.UniqueConstraint('token_jti', name='uq_user_sessions_token_jti'),
    )
    op.create_index('ix_user_sessions_user', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_status', 'user_sessions', ['status'])
    op.create_index('ix_user_sessions_expires', 'user_sessions', ['expires_at'])

    # Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_jti', sa.String(255), nullable=False),
        sa.Column('family_id', sa.String(255), nullable=False),
        sa.Column('is_revoked', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('replaced_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_refresh_tokens_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['replaced_by'], ['refresh_tokens.id'], name='fk_refresh_tokens_replaced_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_refresh_tokens_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_refresh_tokens_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_refresh_tokens'),
        sa.UniqueConstraint('token_jti', name='uq_refresh_tokens_token_jti'),
    )
    op.create_index('ix_refresh_tokens_user', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_family', 'refresh_tokens', ['family_id'])
    op.create_index('ix_refresh_tokens_expires', 'refresh_tokens', ['expires_at'])

    print("✓ Identity domain: 7 tables created")

    # ========================================
    # TRANSACTION DOMAIN (10 tables)
    # ========================================

    # Currencies table (reference)
    op.create_table(
        'currencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('code', currency_code, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=True),
        sa.Column('decimal_places', sa.Integer, nullable=False, server_default='2'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_currencies_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_currencies_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_currencies'),
        sa.UniqueConstraint('code', name='uq_currencies_code'),
    )
    op.create_index('ix_currencies_code', 'currencies', ['code'])

    # Payment methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('payment_method_type', payment_method_type, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_2fa', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('daily_limit', sa.Numeric(18, 2), nullable=True),
        sa.Column('monthly_limit', sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_payment_methods_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_payment_methods_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_payment_methods'),
        sa.UniqueConstraint('name', name='uq_payment_methods_name'),
    )
    op.create_index('ix_payment_methods_type', 'payment_methods', ['payment_method_type'])

    # Transaction types table
    op.create_table(
        'transaction_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('transaction_type', transaction_type_value, nullable=False),
        sa.Column('is_debit', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_approval', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('daily_limit', sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_transaction_types_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_transaction_types_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_transaction_types'),
        sa.UniqueConstraint('name', name='uq_transaction_types_name'),
    )
    op.create_index('ix_transaction_types_type', 'transaction_types', ['transaction_type'])

    # Transaction statuses table
    op.create_table(
        'transaction_statuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('status_value', transaction_status_value, nullable=False),
        sa.Column('is_terminal', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_failure', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('can_retry', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('next_statuses', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_transaction_statuses_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_transaction_statuses_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_transaction_statuses'),
        sa.UniqueConstraint('status_value', name='uq_transaction_statuses_value'),
    )
    op.create_index('ix_transaction_statuses_value', 'transaction_statuses', ['status_value'])

    # Risk levels table
    op.create_table(
        'risk_levels',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('risk_level', risk_level_value, nullable=False),
        sa.Column('score_min', sa.Integer, nullable=False),
        sa.Column('score_max', sa.Integer, nullable=False),
        sa.Column('color_code', sa.String(7), nullable=True),
        sa.Column('action_required', risk_decision, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_risk_levels_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_risk_levels_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_risk_levels'),
        sa.UniqueConstraint('risk_level', name='uq_risk_levels_level'),
        sa.CheckConstraint('score_min >= 0', name='ck_risk_levels_score_min'),
        sa.CheckConstraint('score_max <= 1000', name='ck_risk_levels_score_max'),
        sa.CheckConstraint('score_min < score_max', name='ck_risk_levels_score_range'),
    )
    op.create_index('ix_risk_levels_level', 'risk_levels', ['risk_level'])

    # Merchants table
    op.create_table(
        'merchants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('merchant_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('merchant_metadata', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('risk_score', sa.Integer, nullable=True),
        sa.Column('rating', sa.Numeric(3, 2), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_merchants_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_merchants_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_merchants'),
        sa.UniqueConstraint('merchant_id', name='uq_merchants_merchant_id'),
    )
    op.create_index('ix_merchants_merchant_id', 'merchants', ['merchant_id'])
    op.create_index('ix_merchants_category', 'merchants', ['category'])

    # Agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('agent_code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('agent_location', sa.String(255), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('agent_metadata', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('agent_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('total_transactions', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_volume', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_agents_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_agents_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_agents'),
        sa.UniqueConstraint('agent_code', name='uq_agents_agent_code'),
    )
    op.create_index('ix_agents_code', 'agents', ['agent_code'])
    op.create_index('ix_agents_country', 'agents', ['country'])

    # Devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('os_type', sa.String(50), nullable=True),
        sa.Column('os_version', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(50), nullable=True),
        sa.Column('browser_version', sa.String(50), nullable=True),
        sa.Column('app_version', sa.String(50), nullable=True),
        sa.Column('device_metadata', JSONB, nullable=True),
        sa.Column('is_trusted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_devices_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_devices_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_devices'),
        sa.UniqueConstraint('device_id', name='uq_devices_device_id'),
    )
    op.create_index('ix_devices_device_id', 'devices', ['device_id'])
    op.create_index('ix_devices_type', 'devices', ['device_type'])

    # Locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('street_address', sa.String(500), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('location_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_locations_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_locations_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_locations'),
    )
    op.create_index('ix_locations_country', 'locations', ['country'])
    op.create_index('ix_locations_coordinates', 'locations', ['latitude', 'longitude'])

    # Transactions table (core entity)
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('transaction_reference', sa.String(100), nullable=False),
        sa.Column('external_reference', sa.String(100), nullable=True),
        sa.Column('sender_identifier', sa.String(100), nullable=True),
        sa.Column('receiver_identifier', sa.String(100), nullable=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('currency_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_level_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('fee', sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('exchange_rate', sa.Numeric(18, 8), nullable=True),
        sa.Column('transaction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('channel', transaction_channel, nullable=True),
        sa.Column('source_system', source_system, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('transaction_metadata', JSONB, nullable=True),
        sa.Column('risk_score', sa.Integer, nullable=True),
        sa.Column('risk_factors', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], name='fk_transactions_merchant_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], name='fk_transactions_agent_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], name='fk_transactions_device_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name='fk_transactions_location_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], name='fk_transactions_currency_id'),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id'], name='fk_transactions_payment_method_id'),
        sa.ForeignKeyConstraint(['transaction_type_id'], ['transaction_types.id'], name='fk_transactions_transaction_type_id'),
        sa.ForeignKeyConstraint(['status_id'], ['transaction_statuses.id'], name='fk_transactions_status_id'),
        sa.ForeignKeyConstraint(['risk_level_id'], ['risk_levels.id'], name='fk_transactions_risk_level_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_transactions_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_transactions_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_transactions'),
        sa.UniqueConstraint('transaction_reference', name='uq_transactions_reference'),
        sa.CheckConstraint('amount >= 0', name='ck_transactions_amount_positive'),
        sa.CheckConstraint('fee >= 0', name='ck_transactions_fee_positive'),
        sa.CheckConstraint('net_amount >= 0', name='ck_transactions_net_amount_positive'),
        sa.CheckConstraint('risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1000)', name='ck_transactions_risk_score'),
    )
    op.create_index('ix_transactions_reference', 'transactions', ['transaction_reference'])
    op.create_index('ix_transactions_user_created', 'transactions', ['created_by', 'created_at'])
    op.create_index('ix_transactions_timestamp', 'transactions', ['transaction_timestamp'])
    op.create_index('ix_transactions_status', 'transactions', ['status_id'])
    op.create_index('ix_transactions_amount', 'transactions', ['amount'])
    op.create_index('ix_transactions_metadata', 'transactions', ['transaction_metadata'], postgresql_using='gin')

    print("✓ Transaction domain: 10 tables created")

    # ========================================
    # FRAUD DOMAIN (9 tables)
    # ========================================

    # Fraud rules table
    op.create_table(
        'fraud_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rule_type', detection_method, nullable=False),
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('rule_conditions', JSONB, nullable=False),
        sa.Column('actions', JSONB, nullable=False),
        sa.Column('false_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('true_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('precision', sa.Numeric(5, 4), nullable=True),
        sa.Column('last_triggered', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_fraud_rules_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_fraud_rules_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_fraud_rules'),
        sa.UniqueConstraint('rule_name', name='uq_fraud_rules_name'),
    )
    op.create_index('ix_fraud_rules_name', 'fraud_rules', ['rule_name'])
    op.create_index('ix_fraud_rules_active', 'fraud_rules', ['is_active', 'priority'])
    op.create_index('ix_fraud_rules_conditions', 'fraud_rules', ['rule_conditions'], postgresql_using='gin')

    # Fraud alerts table
    op.create_table(
        'fraud_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_severity', alert_severity, nullable=False),
        sa.Column('alert_status', alert_status, nullable=False, server_default='new'),
        sa.Column('alert_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('alert_reasons', JSONB, nullable=False),
        sa.Column('alert_metadata', JSONB, nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_fraud_alerts_transaction_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['fraud_rules.id'], name='fk_fraud_alerts_rule_id'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name='fk_fraud_alerts_assigned_to'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_fraud_alerts_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_fraud_alerts_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_fraud_alerts'),
        sa.CheckConstraint('alert_score >= 0 AND alert_score <= 100', name='ck_fraud_alerts_score'),
    )
    op.create_index('ix_fraud_alerts_transaction', 'fraud_alerts', ['transaction_id'])
    op.create_index('ix_fraud_alerts_rule', 'fraud_alerts', ['rule_id'])
    op.create_index('ix_fraud_alerts_status', 'fraud_alerts', ['alert_status'])
    op.create_index('ix_fraud_alerts_severity', 'fraud_alerts', ['alert_severity'])
    op.create_index('ix_fraud_alerts_score', 'fraud_alerts', ['alert_score'])
    op.create_index('ix_fraud_alerts_created', 'fraud_alerts', ['created_at'])

    # Fraud cases table
    op.create_table(
        'fraud_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('case_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('case_priority', case_priority, nullable=False, server_default='medium'),
        sa.Column('case_status', case_status, nullable=False, server_default='new'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_type', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('estimated_loss', sa.Numeric(18, 2), nullable=True),
        sa.Column('actual_loss', sa.Numeric(18, 2), nullable=True),
        sa.Column('case_metadata', JSONB, nullable=True),
        sa.Column('is_escalated', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('escalation_reason', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name='fk_fraud_cases_assigned_to'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_fraud_cases_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_fraud_cases_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_fraud_cases'),
        sa.UniqueConstraint('case_number', name='uq_fraud_cases_case_number'),
        sa.CheckConstraint('estimated_loss IS NULL OR estimated_loss >= 0', name='ck_fraud_cases_estimated_loss'),
        sa.CheckConstraint('actual_loss IS NULL OR actual_loss >= 0', name='ck_fraud_cases_actual_loss'),
    )
    op.create_index('ix_fraud_cases_number', 'fraud_cases', ['case_number'])
    op.create_index('ix_fraud_cases_status', 'fraud_cases', ['case_status'])
    op.create_index('ix_fraud_cases_priority', 'fraud_cases', ['case_priority'])
    op.create_index('ix_fraud_cases_assigned', 'fraud_cases', ['assigned_to'])

    # Risk assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_score', sa.Integer, nullable=False),
        sa.Column('risk_level', risk_level_value, nullable=False),
        sa.Column('risk_decision', risk_decision, nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('model_version_id', sa.String(100), nullable=True),
        sa.Column('assessment_factors', JSONB, nullable=True),
        sa.Column('mitigation_recommendations', JSONB, nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_risk_assessments_transaction_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name='fk_risk_assessments_reviewed_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_risk_assessments_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_risk_assessments_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_risk_assessments'),
        sa.UniqueConstraint('transaction_id', name='uq_risk_assessments_transaction'),
        sa.CheckConstraint('assessment_score >= 0 AND assessment_score <= 1000', name='ck_risk_assessments_score'),
        sa.CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)', name='ck_risk_assessments_confidence'),
    )
    op.create_index('ix_risk_assessments_transaction', 'risk_assessments', ['transaction_id'])
    op.create_index('ix_risk_assessments_score', 'risk_assessments', ['assessment_score'])
    op.create_index('ix_risk_assessments_decision', 'risk_assessments', ['risk_decision'])

    # Investigation timeline table
    op.create_table(
        'investigation_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', timeline_action_type, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action_metadata', JSONB, nullable=True),
        sa.Column('previous_status', case_status, nullable=True),
        sa.Column('new_status', case_status, nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['fraud_cases.id'], name='fk_investigation_timeline_case_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], name='fk_investigation_timeline_performed_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_investigation_timeline_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_investigation_timeline_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_investigation_timeline'),
    )
    op.create_index('ix_investigation_timeline_case', 'investigation_timeline', ['case_id'])
    op.create_index('ix_investigation_timeline_action', 'investigation_timeline', ['action_type'])
    op.create_index('ix_investigation_timeline_performed', 'investigation_timeline', ['performed_at'])

    # Fraud comments table
    op.create_table(
        'fraud_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_text', sa.Text, nullable=False),
        sa.Column('comment_visibility', comment_visibility, nullable=False, server_default='internal'),
        sa.Column('is_internal', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reply_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comment_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['fraud_cases.id'], name='fk_fraud_comments_case_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='fk_fraud_comments_author_id'),
        sa.ForeignKeyConstraint(['reply_to'], ['fraud_comments.id'], name='fk_fraud_comments_reply_to'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_fraud_comments_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_fraud_comments_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_fraud_comments'),
    )
    op.create_index('ix_fraud_comments_case', 'fraud_comments', ['case_id'])
    op.create_index('ix_fraud_comments_author', 'fraud_comments', ['author_id'])
    op.create_index('ix_fraud_comments_visibility', 'fraud_comments', ['comment_visibility'])

    # Fraud attachments table
    op.create_table(
        'fraud_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(1024), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('attachment_type', attachment_type, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_evidence', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('download_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('attachment_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['fraud_cases.id'], name='fk_fraud_attachments_case_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_fraud_attachments_uploaded_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_fraud_attachments_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_fraud_attachments_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_fraud_attachments'),
    )
    op.create_index('ix_fraud_attachments_case', 'fraud_attachments', ['case_id'])
    op.create_index('ix_fraud_attachments_type', 'fraud_attachments', ['attachment_type'])
    op.create_index('ix_fraud_attachments_uploaded', 'fraud_attachments', ['uploaded_by'])

    # Predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', sa.String(100), nullable=False),
        sa.Column('predicted_label', prediction_label, nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('probability_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('inference_time_ms', sa.Integer, nullable=True),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('prediction_metadata', JSONB, nullable=True),
        sa.Column('explanation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_predictions_transaction_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_predictions_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_predictions_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_predictions'),
        sa.CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)', name='ck_predictions_confidence'),
        sa.CheckConstraint('probability_score IS NULL OR (probability_score >= 0 AND probability_score <= 1)', name='ck_predictions_probability'),
        sa.CheckConstraint('inference_time_ms IS NULL OR inference_time_ms >= 0', name='ck_predictions_latency'),
    )
    op.create_index('ix_predictions_transaction', 'predictions', ['transaction_id', 'prediction_timestamp'])
    op.create_index('ix_predictions_model', 'predictions', ['model_version_id', 'prediction_timestamp'])
    op.create_index('ix_predictions_timestamp', 'predictions', ['prediction_timestamp'])
    op.create_index('ix_predictions_label', 'predictions', ['predicted_label'])

    # Prediction explanations table
    op.create_table(
        'prediction_explanations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('explanation_method', explanation_method, nullable=False),
        sa.Column('explanation_data', JSONB, nullable=False),
        sa.Column('feature_contributions', JSONB, nullable=True),
        sa.Column('top_features', JSONB, nullable=True),
        sa.Column('shap_values', JSONB, nullable=True),
        sa.Column('lime_weights', JSONB, nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], name='fk_prediction_explanations_prediction_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_prediction_explanations_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_prediction_explanations_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_prediction_explanations'),
    )
    op.create_index('ix_prediction_explanations_prediction', 'prediction_explanations', ['prediction_id'])
    op.create_index('ix_prediction_explanations_method', 'prediction_explanations', ['explanation_method'])

    print("✓ Fraud domain: 8 tables created")

    # ========================================
    # MACHINE LEARNING DOMAIN (7 tables)
    # ========================================

    # Dataset metadata table
    op.create_table(
        'dataset_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('dataset_name', sa.String(255), nullable=False),
        sa.Column('source', dataset_source, nullable=False),
        sa.Column('record_count', sa.Integer, nullable=False),
        sa.Column('feature_count', sa.Integer, nullable=False),
        sa.Column('target_column', sa.String(255), nullable=True),
        sa.Column('hash', sa.String(64), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('schema_definition', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_dataset_metadata_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_dataset_metadata_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_dataset_metadata'),
        sa.UniqueConstraint('dataset_name', name='uq_dataset_metadata_name'),
        sa.UniqueConstraint('hash', name='uq_dataset_metadata_hash'),
        sa.CheckConstraint('record_count >= 0', name='ck_dataset_metadata_records'),
        sa.CheckConstraint('feature_count >= 0', name='ck_dataset_metadata_features'),
    )
    op.create_index('ix_dataset_metadata_name', 'dataset_metadata', ['dataset_name'])
    op.create_index('ix_dataset_metadata_source', 'dataset_metadata', ['source'])

    # Training runs table
    op.create_table(
        'training_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('run_name', sa.String(255), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('training_status', training_status, nullable=False, server_default='pending'),
        sa.Column('random_seed', sa.Integer, nullable=True),
        sa.Column('git_commit_hash', sa.String(40), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('hyperparameters', JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['dataset_metadata.id'], name='fk_training_runs_dataset_id'),
        sa.ForeignKeyConstraint(['initiated_by'], ['users.id'], name='fk_training_runs_initiated_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_training_runs_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_training_runs_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_training_runs'),
        sa.CheckConstraint('duration_seconds IS NULL OR duration_seconds >= 0', name='ck_training_runs_duration_positive'),
    )
    op.create_index('ix_training_runs_dataset', 'training_runs', ['dataset_id'])
    op.create_index('ix_training_runs_status', 'training_runs', ['training_status'])
    op.create_index('ix_training_runs_started', 'training_runs', ['started_at'])

    # Model versions table
    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('algorithm', algorithm_type, nullable=False),
        sa.Column('framework', framework_type, nullable=False),
        sa.Column('artifact_path', sa.String(1024), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('training_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', model_status, nullable=False, server_default='draft'),
        sa.Column('deployed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deployment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('hyperparameters', JSONB, nullable=True),
        sa.Column('training_duration_seconds', sa.Integer, nullable=True),
        sa.Column('model_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['training_run_id'], ['training_runs.id'], name='fk_model_versions_training_run_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_model_versions_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_model_versions_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_model_versions'),
    )
    op.create_index('ix_model_versions_name', 'model_versions', ['model_name', 'version_number'], unique=True)
    op.create_index('ix_model_versions_model_name', 'model_versions', ['model_name'])
    op.create_index('ix_model_versions_status', 'model_versions', ['status'])
    op.create_index('ix_model_versions_deployed', 'model_versions', ['deployed'])
    op.create_index('ix_model_versions_training_run', 'model_versions', ['training_run_id'])

    # Model metrics table
    op.create_table(
        'model_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accuracy', sa.Numeric(5, 4), nullable=True),
        sa.Column('precision', sa.Numeric(5, 4), nullable=True),
        sa.Column('recall', sa.Numeric(5, 4), nullable=True),
        sa.Column('f1_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('roc_auc', sa.Numeric(5, 4), nullable=True),
        sa.Column('log_loss', sa.Numeric(10, 6), nullable=True),
        sa.Column('false_positive_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('false_negative_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('evaluation_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('evaluation_dataset_hash', sa.String(64), nullable=True),
        sa.Column('mean_absolute_error', sa.Numeric(10, 6), nullable=True),
        sa.Column('mean_squared_error', sa.Numeric(10, 6), nullable=True),
        sa.Column('r2_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('metrics_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_model_metrics_model_version_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_model_metrics_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_model_metrics_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_model_metrics'),
        sa.UniqueConstraint('model_version_id', name='uq_model_metrics_version'),
        sa.CheckConstraint('accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)', name='ck_model_metrics_accuracy'),
        sa.CheckConstraint('precision IS NULL OR (precision >= 0 AND precision <= 1)', name='ck_model_metrics_precision'),
        sa.CheckConstraint('recall IS NULL OR (recall >= 0 AND recall <= 1)', name='ck_model_metrics_recall'),
        sa.CheckConstraint('f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1)', name='ck_model_metrics_f1'),
        sa.CheckConstraint('roc_auc IS NULL OR (roc_auc >= 0 AND roc_auc <= 1)', name='ck_model_metrics_roc_auc'),
        sa.CheckConstraint('false_positive_rate IS NULL OR (false_positive_rate >= 0 AND false_positive_rate <= 1)', name='ck_model_metrics_fpr'),
        sa.CheckConstraint('false_negative_rate IS NULL OR (false_negative_rate >= 0 AND false_negative_rate <= 1)', name='ck_model_metrics_fnr'),
    )
    op.create_index('ix_model_metrics_version', 'model_metrics', ['model_version_id'])
    op.create_index('ix_model_metrics_timestamp', 'model_metrics', ['evaluation_timestamp'])

    # Feature importance table
    op.create_table(
        'feature_importance',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature_name', sa.String(255), nullable=False),
        sa.Column('importance_score', sa.Numeric(10, 8), nullable=True),
        sa.Column('ranking', sa.Integer, nullable=True),
        sa.Column('importance_type', sa.String(50), nullable=True),
        sa.Column('importance_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_feature_importance_model_version_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_feature_importance_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_feature_importance_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_feature_importance'),
        sa.UniqueConstraint('model_version_id', 'feature_name', name='uq_feature_importance_model_feature'),
        sa.CheckConstraint('importance_score IS NULL OR (importance_score >= 0 AND importance_score <= 1)', name='ck_feature_importance_score'),
        sa.CheckConstraint('ranking IS NULL OR ranking > 0', name='ck_feature_importance_ranking'),
    )
    op.create_index('ix_feature_importance_model', 'feature_importance', ['model_version_id'])
    op.create_index('ix_feature_importance_ranking', 'feature_importance', ['model_version_id', 'ranking'])

    # Prediction history table
    op.create_table(
        'prediction_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('prediction_id', sa.String(255), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('status', prediction_status_enum, nullable=False, server_default='completed'),
        sa.Column('input_features_hash', sa.String(64), nullable=True),
        sa.Column('prediction_result', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('prediction_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_prediction_history_transaction_id'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name='fk_prediction_history_model_version_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_prediction_history_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_prediction_history_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_prediction_history'),
        sa.UniqueConstraint('prediction_id', name='uq_prediction_history_prediction_id'),
        sa.CheckConstraint('latency_ms IS NULL OR latency_ms >= 0', name='ck_prediction_history_latency'),
    )
    op.create_index('ix_prediction_history_transaction', 'prediction_history', ['transaction_id'])
    op.create_index('ix_prediction_history_model', 'prediction_history', ['model_version_id'])
    op.create_index('ix_prediction_history_timestamp', 'prediction_history', ['prediction_timestamp'])
    op.create_index('ix_prediction_history_status', 'prediction_history', ['status'])

    # Model registry table
    op.create_table(
        'model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('current_version', sa.Integer, nullable=False),
        sa.Column('previous_version', sa.Integer, nullable=True),
        sa.Column('rollback_version', sa.Integer, nullable=True),
        sa.Column('deployment_environment', deployment_environment, nullable=False, server_default='production'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('deployment_notes', sa.Text, nullable=True),
        sa.Column('registry_metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['deployed_by'], ['users.id'], name='fk_model_registry_deployed_by'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_model_registry_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], name='fk_model_registry_updated_by'),
        sa.PrimaryKeyConstraint('id', name='pk_model_registry'),
        sa.UniqueConstraint('model_name', name='uq_model_registry_model_name'),
    )
    op.create_index('ix_model_registry_name', 'model_registry', ['model_name'])
    op.create_index('ix_model_registry_environment', 'model_registry', ['deployment_environment'])
    op.create_index('ix_model_registry_active', 'model_registry', ['is_active'])

    print("✓ ML domain: 7 tables created")
    print("\n✓✓✓ INITIAL SCHEMA CREATION COMPLETE ✓✓✓")
    print("  - 31 ENUM types")
    print("  - 33 tables")
    print("  - 100+ indexes")
    print("  - 50+ constraints")


def downgrade() -> None:
    """
    Downgrade database schema.

    Drops all tables and enums in reverse dependency order:
    1. Dependent entities first (predictions, alerts, etc.)
    2. Core entities second (transactions, users, etc.)
    3. Reference tables last (currencies, payment_methods)
    4. ENUM types last (no dependencies)
    """
    # Drop ML domain tables
    op.drop_table('model_registry')
    op.drop_table('prediction_history')
    op.drop_table('feature_importance')
    op.drop_table('model_metrics')
    op.drop_table('model_versions')
    op.drop_table('training_runs')
    op.drop_table('dataset_metadata')

    # Drop fraud domain tables
    op.drop_table('fraud_attachments')
    op.drop_table('fraud_comments')
    op.drop_table('investigation_timeline')
    op.drop_table('risk_assessments')
    op.drop_table('fraud_cases')
    op.drop_table('prediction_explanations')
    op.drop_table('predictions')
    op.drop_table('fraud_rules')
    op.drop_table('fraud_alerts')

    # Drop transaction domain tables
    op.drop_table('transactions')
    op.drop_table('locations')
    op.drop_table('devices')
    op.drop_table('agents')
    op.drop_table('merchants')
    op.drop_table('risk_levels')
    op.drop_table('transaction_statuses')
    op.drop_table('transaction_types')
    op.drop_table('payment_methods')
    op.drop_table('currencies')

    # Drop identity domain tables
    op.drop_table('refresh_tokens')
    op.drop_table('user_sessions')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('users', checkfirst=False)
    op.drop_table('roles', checkfirst=False)
    op.drop_table('permissions', checkfirst=False)

    # Drop ENUM types in reverse order
    enums = [
        'dataset_source', 'framework_type', 'algorithm_type',
        'prediction_status', 'deployment_environment', 'model_status',
        'training_status', 'explanation_method', 'attachment_type',
        'comment_visibility', 'timeline_action_type', 'risk_decision',
        'prediction_label', 'detection_method', 'case_status',
        'case_priority', 'alert_status', 'alert_severity',
        'transaction_type_value', 'payment_method_type',
        'currency_code', 'source_system', 'transaction_channel',
        'risk_level_value', 'transaction_status_value',
        'authentication_provider', 'token_type',
        'session_status', 'permission_action', 'role_type', 'user_status'
    ]

    for enum_name in enums:
        try:
            op.execute(f'DROP TYPE IF EXISTS {enum_name}')
        except:
            pass

    print("✓ Database schema downgraded to base")
