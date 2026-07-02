# Database Setup Guide

## Overview

This guide covers the database setup for FraudWatch, including PostgreSQL configuration, migrations, and verification.

## Prerequisites

- PostgreSQL 15+ installed and running
- Python 3.11+
- Alembic 1.12.1
- SQLAlchemy 2.0.23

## Quick Start

### 1. Install PostgreSQL

```bash
# macOS (Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt install postgresql-15
sudo systemctl start postgresql

# Verify installation
psql --version
```

### 2. Create Database

```bash
# Create development database
psql -U postgres -c "CREATE DATABASE fraudwatch_dev;"

# Create testing database
psql -U postgres -c "CREATE DATABASE fraudwatch_test;"

# Create user (if needed)
psql -U postgres -c "CREATE USER fraudwatch WITH PASSWORD 'fraudwatch';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fraudwatch_dev TO fraudwatch;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fraudwatch_test TO fraudwatch;"
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file in `backend/` directory:

```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://fraudwatch:fraudwatch@localhost:5432/fraudwatch_dev
DATABASE_SYNC_URL=postgresql://fraudwatch:fraudwatch@localhost:5432/fraudwatch_dev
DATABASE_ECHO=false
```

### 5. Install Alembic

```bash
cd backend
alembic init alembic
```

This creates the `alembic/` directory with:
- `env.py` - Migration environment configuration
- `script.py.mako` - Migration file template
- `versions/` - Migration files directory

## Database Schema

The FraudWatch database consists of:

### 32 Tables Across 4 Domains

**Identity Domain (6 tables)**
- users
- roles
- permissions
- role_permissions
- user_roles (association)
- user_sessions
- refresh_tokens

**Transaction Domain (10 tables)**
- currencies
- payment_methods
- transaction_types
- transaction_statuses
- risk_levels
- merchants
- agents
- devices
- locations
- transactions

**Fraud Domain (9 tables)**
- fraud_alerts
- fraud_cases
- fraud_rules
- predictions
- prediction_explanations
- risk_assessments
- investigation_timeline
- fraud_comments
- fraud_attachments

**Machine Learning Domain (7 tables)**
- dataset_metadata
- training_runs
- model_versions
- model_metrics
- feature_importance
- prediction_history
- model_registry

### 31 ENUM Types

- Identity: 6 enums (user_status, role_type, etc.)
- Transaction: 7 enums (transaction_status_value, risk_level_value, etc.)
- Fraud: 10 enums (alert_severity, alert_status, etc.)
- ML: 8 enums (training_status, model_status, etc.)

## Migration Commands

### Generate Migration

```bash
cd backend

# Autogenerate migration from model changes
alembic revision --autogenerate -m "description"

# Create empty migration
alembic revision -m "description"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade 001_initial_schema

# Upgrade one step
alembic upgrade +1
```

### Rollback Migrations

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001_initial_schema

# Downgrade to base (remove all migrations)
alembic downgrade base
```

### Check Migration Status

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Initial Migration

The initial migration (`001_initial_schema.py`) creates the complete database schema:

```bash
# Ensure database exists
psql -U postgres -c "CREATE DATABASE fraudwatch_dev;"

# Run migration
cd backend
alembic upgrade head
```

## Verification

```bash
# Run verification script
python validate_orm.py

# Check tables created
psql -U fraudwatch -d fraudwatch_dev -c "\dt"

# Check ENUMs created
psql -U fraudwatch -d fraudwatch_dev -c "\dT"

# Check indexes
psql -U fraudwatch -d fraudwatch_dev -c "\di"
```

## Troubleshooting

### Migration Fails with "relation does not exist"

Ensure you're using the correct migration order:
```bash
alembic downgrade base
alembic upgrade head
```

### ENUM Type Errors

PostgreSQL ENUMs must be dropped in reverse order:
```sql
DROP TYPE IF EXISTS dataset_source CASCADE;
```

### Connection Refused

Check PostgreSQL is running:
```bash
# macOS
brew services list

# Ubuntu
sudo systemctl status postgresql

# Check port
netstat -an | grep 5432
```

## Backup & Restore

```bash
# Backup
pg_dump -U fraudwatch fraudwatch_dev > backup.sql

# Restore
psql -U fraudwatch fraudwatch_dev < backup.sql
```

## Next Steps

After database setup, proceed to:
1. Seeders (initial data)
2. Connection pooling configuration
3. Database monitoring