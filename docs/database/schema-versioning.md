# Schema Versioning Strategy

## Overview

This document describes the database schema versioning strategy for FraudWatch, including how migrations are organized, named, and managed over time.

## Versioning Principles

### Semantic Versioning for Database

FraudWatch uses a date-based migration naming convention aligned with semantic versioning:

```
YYYYMMDDHHMM_description.py
```

**Example:**
```
202601201200_initial_schema.py
202601211030_add_mfa_fields.py
202601221400_create_fraud_alerts.py
```

### Migration State Machine

```
[base] ──→ [001_initial_schema] ──→ [002_add_mfa] ──→ [003_add_fraud_alerts] ──→ [head]
              ↑__________________________|
                    (downgrade/upgrade)
```

**States:**
- `base`: Empty database (no migrations applied)
- `head`: Latest migration
- `current`: Currently applied migration

## Migration Organization

### Directory Structure

```
backend/alembic/
├── env.py                    # Migration environment
├── script.py.mako            # Migration template
├── README.md                 # Alembic instructions
├── alembic.ini               # Alembic configuration
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_user_mfa.py
    ├── 003_create_fraud_alerts.py
    └── ...
```

### Naming Convention

**Format:** `{sequence:03d}_{description}.py`

**Sequence:** Incrementing number (001, 002, 003...)
**Description:** Brief, lowercase, underscore-separated description

**Examples:**
- ✅ Good: `004_add_transaction_risk_score.py`
- ❌ Bad: `fix_stuff.py`
- ❌ Bad: `add new column.py`

## Migration Types

### 1. Schema Migrations

Changes to database structure (tables, columns, indexes, constraints):

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean, nullable=False))
    op.create_index('ix_users_mfa', 'users', ['mfa_enabled'])

def downgrade() -> None:
    op.drop_index('ix_users_mfa')
    op.drop_column('users', 'mfa_enabled')
```

### 2. Data Migrations

Changes to data within existing schema:

```python
def upgrade() -> None:
    # Populate new column from existing data
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET full_name = first_name || ' ' || last_name"
    )

def downgrade() -> None:
    connection = op.get_bind()
    connection.execute("UPDATE users SET full_name = NULL")
```

### 3. Maintenance Migrations

Database maintenance operations:

```python
def upgrade() -> None:
    # Rebuild indexes
    op.execute("REINDEX INDEX ix_users_email")
    
    # Vacuum analyze
    op.execute("VACUUM ANALYZE users")
    
    # Update statistics
    op.execute("ANALYZE users")

def downgrade() -> None:
    pass  # Maintenance operations don't need downgrade
```

## Version History Management

### Viewing History

```bash
# Show all migrations
alembic history --verbose

# Show migration graph
alembic history --verbose --format=ascii

# Show current version
alembic current --verbose
```

### Understanding Migration States

| State | Description | Action Required |
|-------|-------------|-----------------|
| `current` | Applied and up-to-date | None |
| `pending` | Not yet applied | Run `alembic upgrade` |
| `conflict` | Two heads exist | Merge migrations |
| `detached` | Branch without parent | Downgrade to base, then upgrade |

### Branching Strategy

**Main Branch:**
```
001 → 002 → 003 → 004 → 005 (head)
```

**Feature Branch:**
```
001 → 002 → 003 → 006_feature_add_fraud_alerts
```

**Merge:**
```
001 → 002 → 003 → 004 → 005 (head)
              ↘ 006 → 007_merge_006_005 ↗
```

**Merging Migrations:**
```bash
# When two developers create migrations on different branches
alembic merge -m "merge_user_and_fraud_branches" 005 006
```

## Migration Best Practices

### 1. Atomic Changes

Each migration should represent a single logical change:

```python
# ✅ Good - One change
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.create_index('ix_users_phone', 'users', ['phone'])

# ❌ Bad - Multiple unrelated changes
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.create_table('fraud_alerts', ...)
    op.add_column('transactions', sa.Column('risk_score', sa.Float, nullable=True))
```

### 2. Reversible Operations

Always implement `downgrade()`:

```python
# ✅ Good - Fully reversible
def upgrade() -> None:
    op.create_table('users', ...)
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade() -> None:
    op.drop_index('ix_users_email')
    op.drop_table('users')

# ⚠️  Acceptable - Irreversible (data loss)
def downgrade() -> None:
    # Data migration that can't be undone
    pass
```

### 3. Backward Compatibility

Never break existing code:

```python
# ✅ Good - Add column with default
def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('status', sa.String(50), nullable=False, server_default='active')
    )

# ❌ Bad - Break existing queries
def upgrade() -> None:
    op.alter_column('users', 'email', new_column_name='user_email')
```

### 4. Idempotency

Migrations should be safe to run multiple times:

```python
# ✅ Good - Check before creating
def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute("SELECT to_regclass('ix_users_email')")
    if not result.fetchone()[0]:
        op.create_index('ix_users_email', 'users', ['email'])

# ❌ Bad - Will fail if run twice
def upgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
```

## Migration Workflow

### Developer Workflow

```bash
# 1. Pull latest code
git pull origin main

# 2. Upgrade to latest
alembic upgrade head

# 3. Make model changes
# Edit app/models/user.py

# 4. Generate migration
alembic revision --autogenerate -m "add_user_mfa_fields"

# 5. Review migration
vim alembic/versions/004_add_user_mfa_fields.py

# 6. Test migration
alembic downgrade -1
alembic upgrade head

# 7. Commit
git add alembic/versions/004_add_user_mfa_fields.py
git commit -m "feat: add user MFA fields"
git push origin feature/add-user-mfa
```

### Code Review Checklist

- [ ] Migration has descriptive message
- [ ] Upgrade and downgrade are both implemented
- [ ] Downgrade reverses upgrade (reverse order)
- [ ] ENUMs created before tables, dropped after
- [ ] Foreign keys added after tables
- [ ] Indexes created with appropriate names
- [ ] Server defaults used for non-nullable columns
- [ ] No hardcoded values (use constants)
- [ ] Tested on fresh database
- [ ] Tested upgrade/downgrade cycle

## Production Deployment

### Pre-Deployment

```bash
# 1. Create backup
pg_dump -U fraudwatch fraudwatch_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test on staging
alembic upgrade head

# 3. Review migration
cat alembic/versions/$(alembic current | grep "Current revision" | awk '{print $3}').py

# 4. Estimate impact
psql -U fraudwatch -d fraudwatch_prod -c "SELECT count(*) FROM users;"
```

### Deployment

```bash
# 1. Notify team
# Post in #devops channel

# 2. Stop application (if needed)
# docker-compose stop backend

# 3. Run migration
alembic upgrade head

# 4. Verify
alembic current
psql -U fraudwatch -d fraudwatch_prod -c "\dt"

# 5. Start application
# docker-compose start backend

# 6. Monitor
tail -f logs/app.log
```

### Rollback

```bash
# If migration fails:
# 1. Restore backup
psql -U fraudwatch fraudwatch_prod < backup_20260120_120000.sql

# 2. Downgrade
alembic downgrade -1

# 3. Start application
docker-compose start backend

# 4. Notify team
```

## Schema Evolution Examples

### Adding a Column

**Migration:**
```python
def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('phone_verified', sa.Boolean, nullable=False, server_default='false')
    )
    op.create_index('ix_users_phone_verified', 'users', ['phone_verified'])

def downgrade() -> None:
    op.drop_index('ix_users_phone_verified')
    op.drop_column('users', 'phone_verified')
```

### Renaming a Column

**Migration:**
```python
def upgrade() -> None:
    op.alter_column('users', 'emial', new_column_name='email')

def downgrade() -> None:
    op.alter_column('users', 'email', new_column_name='emial')
```

### Adding a Foreign Key

**Migration:**
```python
def upgrade() -> None:
    op.add_column('transactions', sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_transactions_merchant_id',
        'transactions', 'merchants',
        ['merchant_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_transactions_merchant', 'transactions', ['merchant_id'])

def downgrade() -> None:
    op.drop_index('ix_transactions_merchant')
    op.drop_constraint('fk_transactions_merchant_id', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'merchant_id')
```

### Creating a Composite Index

**Migration:**
```python
def upgrade() -> None:
    op.create_index(
        'ix_transactions_user_date',
        'transactions',
        ['user_id', 'created_at'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_transactions_user_date')
```

## Monitoring & Auditing

### Track Applied Migrations

```sql
-- View migration history
SELECT 
    version_num,
    (SELECT COUNT(*) FROM alembic_version WHERE version_num <= av.version_num) as migration_count
FROM alembic_version av
ORDER BY version_num DESC;
```

### Detect Long-Running Migrations

```sql
-- Check for active migrations
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
    AND query LIKE '%alembic%'
ORDER BY duration DESC;
```

### Audit Schema Changes

```sql
-- List all tables with creation timestamps
SELECT 
    tablename,
    pg_total_relation_size(tablename) AS size,
    (SELECT created FROM pg_stat_user_tables WHERE relname = tablename) AS created
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY created DESC;

-- List all indexes
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

## Reference

- [Database Migrations Best Practices](https://www.prisma.io/dataguide/intro/database-migrations)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Schema Management](https://www.postgresql.org/docs/current/ddl.html)