# FraudWatch Demo Data Seeder

This module provides comprehensive demo data generation for the FraudWatch fraud detection platform.

## Quick Start

### Prerequisites

1. Ensure the database is running and migrations are applied:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. Run the base seed to create reference data (currencies, payment methods, etc.):
   ```bash
   python -m seed.main
   ```

### Generate Demo Data

```bash
# Seed demo data (50,000 transactions, alerts, cases, ML models, etc.)
python -m seed.demo.main seed

# Reset and regenerate all demo data
python -m seed.demo.main seed --reset

# Verify existing demo data
python -m seed.demo.main verify

# Reset/clear all demo data
python -m seed.demo.main reset
```

## Demo Credentials

After seeding, you can log in with these accounts:

| Email | Password | Role | Description |
|-------|----------|------|-------------|
| admin@fraudwatch.demo | Admin@123 | Super Admin | Full system access |
| analyst@fraudwatch.demo | Analyst@123 | Fraud Analyst | Fraud analysis and monitoring |
| investigator@fraudwatch.demo | Investigator@123 | Investigator | Case investigation and resolution |
| viewer@fraudwatch.demo | Viewer@123 | Viewer | Read-only dashboard access |

## Data Generated

### Users & RBAC
- 4 demo users with different roles
- Complete role-based permissions
- Role assignments

### Transactions (50,000)
- 95% legitimate transactions (47,500)
- 5% fraudulent transactions (2,500)
- Realistic fintech patterns
- Multiple currencies, channels, and payment methods
- Distributed over 90 days

### Fraud Scenarios
The system generates 5 types of fraud patterns:

1. **Account Takeover** (20%)
   - New device, unusual location
   - Risk score: 90-98%
   - Severity: Critical

2. **Transaction Velocity** (25%)
   - Multiple rapid transactions
   - Risk score: 85-95%
   - Severity: High/Critical

3. **Suspicious Merchant** (15%)
   - New merchant, unusual category
   - Risk score: 75-90%
   - Severity: Medium

4. **Location Anomaly** (20%)
   - Impossible travel, VPN/proxy
   - Risk score: 70-85%
   - Severity: High

5. **High Value Fraud** (20%)
   - Unusually large amounts
   - Risk score: 80-95%
   - Severity: Critical

### Fraud Alerts (~1,250)
- 50% of fraud transactions generate alerts
- Severity distribution:
  - Critical: 10%
  - High: 25%
  - Medium: 40%
  - Low: 25%
- Various detection methods (rule-based, ML, hybrid)

### Fraud Cases (300-500)
- 60% of alerts become investigation cases
- Multiple case statuses (new, investigating, escalated, resolved, etc.)
- Investigation timelines and comments
- Evidence JSON for each case

### ML Models
- 6 model types with multiple versions
- Model metrics (accuracy, precision, recall, F1, ROC-AUC)
- Feature importance rankings
- Prediction history (10,000 predictions)
- Model registry entries

### Analytics
- 90 days of historical analytics
- Daily transaction volumes
- Fraud rates and trends
- Channel and payment method breakdowns

## Architecture

```
backend/seed/demo/
├── __init__.py          # Package initialization
├── config.py            # Configuration and constants
├── helpers.py           # Utility functions
├── main.py              # Main entry point
├── users.py             # User and RBAC generation
├── transactions.py      # Transaction generation
├── fraud.py             # Alerts and cases generation
├── ml.py                # ML models and predictions
└── analytics.py         # Analytics data generation
```

## Configuration

Edit `config.py` to customize:

- Number of transactions
- Fraud ratio
- Time range
- Alert/case counts
- ML model definitions
- Fraud scenarios
- Demo user credentials

## Performance

Seeding 50,000 transactions typically takes:
- Users: < 1 second
- Transactions: 30-60 seconds
- Alerts & Cases: 10-20 seconds
- ML Data: 5-10 seconds
- Analytics: 5-10 seconds

**Total: ~1-2 minutes**

## Troubleshooting

### "No currencies found" warning
Run the base seed first:
```bash
python -m seed.main
```

### Database connection errors
Verify your database URL in `.env` or pass it explicitly:
```bash
python -m seed.demo.main seed --database-url postgresql+asyncpg://user:pass@host:5432/dbname
```

### Slow seeding
Reduce `NUM_TRANSACTIONS` in `config.py` or increase database performance.

## Notes

- All passwords are hashed using bcrypt
- Data is idempotent (safe to run multiple times)
- Use `--reset` flag to clear and regenerate all data
- Transactions are batched (10,000 at a time) for memory efficiency
- Foreign key constraints are respected
