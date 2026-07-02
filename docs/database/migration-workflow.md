# Migration Workflow Guide

## Overview

This guide covers the Alembic migration workflow for FraudWatch, including best practices for creating, testing, and deploying database migrations.

## Migration Principles

### 1. Immutability
- Migration files are **never modified** after being committed
- If a migration has an error, create a new migration to fix it
- Each migration represents a specific point in database history

### 2. Version Control
- All migrations are committed to Git
- Migration files are the single source of truth for schema changes
- Never manually modify the database schema in production

### 3. Deterministic
- Migrations produce the same result every time
- No reliance on external state or timing
- Explicit is better than implicit

## Creating Migrations

### Autogenerate Migration (Recommended)

Autogenerate compares SQLAlchemy models to the database and generates migration code:

```bash
cd backend
alembic revision --autogenerate -m "add_fraud_alert_severity_column"
```

**What it detects:**
- New tables
- New columns
- Column type changes
- New indexes
- New foreign keys

**What it doesn't detect:**
- Column renames
- Data migrations
- Schema optimizations (VACUUM, ANALYZE)
- Partial indexes
- CHECK constraints (sometimes)

### Manual Migration

For complex changes that autogenerate can't handle:

```bash
alembic revision -m "add_fraud_detection_function"
```

Then edit the migration file manually.

### Migration Naming Convention

```
{timestamp}_{description}.py
```

Examples:
- `20260120_initial_schema.py`
- `20260121_add_user_mfa_fields.py`
- `20260122_create_fraud_alerts_table.py`

## Migration Structure

### Upgrade Function

The `upgrade()` function applies the migration:

```python
def upgrade() -> None:
    # 1. Create ENUM types (if needed)
    status_enum = postgresql.ENUM('active', 'inactive', name='status_enum')
    status_enum.create(op.get_bind())
    
    # 2. Create tables
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', status_enum, nullable=False),
        # ... other columns
        sa.PrimaryKeyConstraint('id')
    )
    
    # 3. Create indexes
    op.create_index('ix_users_status', 'users', ['status'])
    
    # 4. Add foreign keys
    op.create_foreign_key(
        'fk_users_created_by', 'users', 'users',
        ['created_by'], ['id']
    )
```

### Downgrade Function

The `downgrade()` function reverses the migration:

```python
def downgrade() -> None:
    # Reverse order of upgrade
    op.drop_constraint('fk_users_created_by', 'users', type_='foreignkey')
    op.drop_index('ix_users_status')
    op.drop_table('users')
    
    # Drop ENUM types last
    status_enum = postgresql.ENUM(name='status_enum')
    status_enum.drop(op.get_bind())
```

**Critical Rules:**
1. **Reverse order**: What goes up last, comes down first
2. **Drop constraints before tables**: Foreign keys must be dropped before tables
3. **Drop indexes before constraints**: Some databases require this
4. **Drop ENUMs last**: No dependencies on ENUMs after tables are dropped

## Testing Migrations

### 1. Fresh Database Test

Test the entire migration chain on a clean database:

```bash
# Create fresh database
psql -U postgres -c "DROP DATABASE IF EXISTS fraudwatch_test_fresh;"
psql -U postgres -c "CREATE DATABASE fraudwatch_test_fresh;"

# Run all migrations
cd backend
alembic -x db=fraudwatch_test_fresh upgrade head

# Verify
psql -U fraudwatch -d fraudwatch_test_fresh -c "\dt"
```

### 2. Upgrade/Downgrade Cycle

Test that migrations can be applied and reverted:

```bash
# Upgrade to head
alembic upgrade head

# Check current version
alembic current

# Downgrade one step
alembic downgrade -1

# Verify downgrade succeeded
alembic current

# Upgrade again
alembic upgrade head

# Verify final state
alembic current
```

### 3. Branch Testing

When working on a feature branch:

```bash
# On main branch
alembic upgrade head

# Switch to feature branch
git checkout feature/add-fraud-alerts

# Run new migration
alembic upgrade head

# Test the application

# Switch back to main
git checkout main

# Downgrade to base
alembic downgrade base

# Switch back to feature branch
git checkout feature/add-fraud-alerts

# Upgrade again
alembic upgrade head
```

## Migration Best Practices

### 1. Keep Migrations Small

**Good:**
```python
# One logical change per migration
def upgrade() -> None:
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean, nullable=False, server_default='false'))
    op.create_index('ix_users_mfa_enabled', 'users', ['mfa_enabled'])
```

**Bad:**
```python
# Multiple unrelated changes
def upgrade() -> None:
    # Add MFA
    op.add_column('users', ...)
    # Create fraud detection tables
    op.create_table('fraud_alerts', ...)
    # Add ML models
    op.create_table('model_versions', ...)
    # Fix typo in previous migration
    op.alter_column('users', 'emial', new_column_name='email')
```

### 2. Never Modify Committed Migrations

**Wrong:**
```bash
# Fixing a migration that's already committed
vim alembic/versions/20260120_initial_schema.py
git commit -am "Fix typo in migration"
```

**Correct:**
```bash
# Create a new migration to fix the issue
alembic revision -m "fix_users_email_column_name"
```

### 3. Use Server Defaults

For non-nullable columns on existing tables:

```python
def upgrade() -> None:
    # Add column with server_default
    op.add_column(
        'users',
        sa.Column('status', sa.String(50), nullable=False, server_default='pending_verification')
    )
    
    # Remove server_default after data is populated
    op.alter_column('users', 'status', server_default=None)
```

### 4. Handle ENUMs Carefully

PostgreSQL ENUMs require special handling:

```python
def upgrade() -> None:
    # Create ENUM
    status_enum = postgresql.ENUM('active', 'inactive', name='user_status')
    status_enum.create(op.get_bind())
    
    # Use in table
    op.create_table(
        'users',
        sa.Column('status', status_enum, nullable=False)
    )

def downgrade() -> None:
    # Drop table first
    op.drop_table('users')
    
    # Then drop ENUM
    status_enum = postgresql.ENUM(name='user_status')
    status_enum.drop(op.get_bind())
```

### 5. Use Batch Operations for SQLite

SQLite requires batch mode for certain operations:

```python
def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(255), nullable=False))
        batch_op.create_index('ix_users_email', ['email'])
```

## Data Migrations

### Adding Data Migrations

For populating new columns or tables:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

def upgrade() -> None:
    # 1. Add column
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    
    # 2. Data migration
    connection = op.get_bind()
    session = Session(connection)
    
    users = session.query(User).all()
    for user in users:
        user.full_name = f"{user.first_name} {user.last_name}"
    
    session.commit()
    
    # 3. Make column non-nullable
    op.alter_column('users', 'full_name', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

### Data Migration Best Practices

1. **Use transactions**: Wrap data migrations in transactions
2. **Batch operations**: For large tables, process in batches
3. **Preserve data**: Never delete data in upgrade(), only in downgrade()
4. **Idempotent**: Migration should work even if run twice

## Common Patterns

### Adding a Column

```python
def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('phone_number', sa.String(20), nullable=True)
    )
    op.create_index('ix_users_phone', 'users', ['phone_number'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_users_phone')
    op.drop_column('users', 'phone_number')
```

### Renaming a Column

```python
def upgrade() -> None:
    op.alter_column('users', 'emial', new_column_name='email')

def downgrade() -> None:
    op.alter_column('users', 'email', new_column_name='emial')
```

### Adding a Foreign Key

```python
def upgrade() -> None:
    op.add_column('transactions', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_transactions_user_id',
        'transactions', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_transactions_user_id')
    op.drop_constraint('fk_transactions_user_id', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'user_id')
```

### Creating a Partial Index

```python
def upgrade() -> None:
    op.create_index(
        'ix_users_active_email',
        'users',
        ['email'],
        unique=True,
        postgresql_where=sa.text("status = 'active'")
    )
```

## Troubleshooting

### Migration Conflicts

When two developers create migrations simultaneously:

```bash
# Merge migrations
alembic merge -m "merge_user_and_fraud_migrations" head1 head2
```

### Detached Head Error

```bash
# You're on a branch without a parent
alembic downgrade base
alembic upgrade head
```

### Failed Migration

```bash
# Check current version
alembic current

# Manually fix database if needed
psql -U fraudwatch fraudwatch_dev

# Mark as migrated
alembic stamp head

# Or re-run
alembic downgrade -1
alembic upgrade +1
```

### Autogenerate Not Detecting Changes

Ensure:
1. Models are imported in `env.py`
2. `target_metadata = Base.metadata` is set
3. Models use SQLAlchemy 2.x syntax (`Mapped[]`, `mapped_column()`)

## Production Deployment

### Pre-Deployment Checklist

- [ ] Migration tested on staging database
- [ ] Migration tested on fresh database
- [ ] Downgrade tested
- [ ] Data migration reviewed
- [ ] Backup taken
- [ ] Rollback plan documented

### Deployment Process

```bash
# 1. Backup production database
pg_dump -U fraudwatch fraudwatch_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on staging
cd backend
alembic upgrade head

# 3. Deploy application code (without starting)
# ... (deploy code)

# 4. Run migration
alembic upgrade head

# 5. Verify migration
alembic current
psql -U fraudwatch -d fraudwatch_prod -c "\dt"

# 6. Start application
# ... (start app)

# 7. Monitor for errors
tail -f logs/app.log
```

### Rollback Plan

If migration fails:

```bash
# 1. Stop application
# 2. Restore backup
psql -U fraudwatch fraudwatch_prod < backup_20260120_120000.sql
# 3.Downgrade
alembic downgrade -1
# 4. Start application
```

## Monitoring

### Track Migration History

```sql
-- Check Alembic version table
SELECT * FROM alembic_version ORDER BY version_num DESC;
```

### Monitor Performance

```sql
-- Long-running migrations
SELECT * FROM pg_stat_activity WHERE state = 'active' AND query LIKE '%ALTER%';

-- Table locks
SELECT * FROM pg_locks WHERE NOT granted;
```

## Reference

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/2.0/orm/migration_config.html)
- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)