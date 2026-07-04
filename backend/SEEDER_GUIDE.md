# FraudWatch Database Seeder Guide

## Overview

Production-quality modular seeding framework for populating the database with realistic demo data.

## Quick Start

```bash
# Run all seeders (10,000 transactions by default)
python -m seed.runner

# Run with reset (truncate all tables first)
python -m seed.runner --reset

# Custom transaction count
python -m seed.runner --transactions 50000

# Reset database only
python -m seed.runner --reset-only

# Run specific seeders only
python -m seed.runner --seeders reference identity merchants
```

## Architecture

```
backend/seed/
├── __init__.py
├── base.py                 # BaseSeeder abstract class
├── utils.py                # Faker, Bangladesh locations, helpers
├── runner.py               # CLI entry point, orchestrates all seeders
└── seeders/
    ├── reference_seeder.py     # Currencies, payment methods, types, statuses, risk levels
    ├── identity_seeder.py      # Roles, permissions, users (admin + demo customers)
    ├── merchant_seeder.py      # 50+ realistic merchants
    ├── agent_seeder.py         # 120 wallet agents
    ├── device_seeder.py        # 200 device fingerprints
    ├── location_seeder.py      # 60 Bangladesh locations
    ├── transaction_seeder.py   # 10,000+ transactions with fraud patterns
    ├── fraud_rule_seeder.py    # 10 fraud detection rules
    └── model_registry_seeder.py # ML model metadata
```

## Commands

| Command | Description |
|---------|-------------|
| `python -m seed.runner` | Run all seeders with defaults |
| `python -m seed.runner --reset` | Truncate all tables, then seed |
| `python -m seed.runner --reset-only` | Only truncate all tables |
| `python -m seed.runner --transactions 100000` | Generate 100,000 transactions |
| `python -m seed.runner --seeders reference identity` | Run only specific seeders |
| `python -m seed.runner --seeders transactions --transactions 50000 --reset` | Combined options |

## Seeder Reference

### ReferenceDataSeeder
- Currencies (10): BDT, USD, EUR, GBP, INR, SGD, MYR, SAR, AED, CNY
- Payment Methods (12): bKash, Nagad, Rocket, Visa, Mastercard, etc.
- Transaction Types (10): payment, transfer, withdrawal, deposit, etc.
- Transaction Statuses (8): pending, processing, completed, failed, flagged, etc.
- Risk Levels (4): low, medium, high, critical

### IdentitySeeder
- Permissions (29): granular CRUD + execute per resource
- Roles (5): super_admin, admin, fraud_analyst, compliance_officer, viewer
- RolePermissions: mapped per role
- Admin Users (5): pre-configured staff accounts
- Demo Customers (30): realistic Bangladeshi names

Default password for all users: `FraudWatch@2024`

### MerchantSeeder
- 52 merchants across 12 categories
- Categories: Retail, Restaurant, E-commerce, Utilities, Government, Healthcare, Telecom, Travel, Education, Entertainment, Financial
- Each merchant has: code, name, category, risk rating, location, contact info

### AgentSeeder
- 120 wallet agents
- Distributed across 16 zones
- Location, contact number, status

### DeviceSeeder
- 200 realistic device fingerprints
- Types: Android, iOS, Windows, macOS, Linux, Tablet
- OS, browser, model, fingerprint hash

### LocationSeeder
- 60 Bangladesh locations
- All 8 divisions: Dhaka, Chattogram, Khulna, Rajshahi, Sylhet, Barishal, Rangpur, Mymensingh
- Lat/lng, district, timezone

### TransactionSeeder
- Configurable count (default 10,000)
- ~3% flagged as fraudulent
- 9 fraud pattern types: velocity, impossible_travel, high_value, new_device, dormant, round_amount, card_testing, merchant_abuse, synthetic
- Realistic amount distribution (small:medium:large = 60:25:15)
- Timestamps spread over last 90 days
- Status: completed (57%), pending (14%), flagged (14%), failed (14%)

### FraudRuleSeeder
- 10 fraud detection rules
- Categories: velocity, amount, geography, device, behavioral, attack, merchant, identity
- Severity: critical, high, medium, low

### ModelRegistrySeeder
- 5 ML model entries
- Algorithms: XGBoost, Random Forest, Isolation Forest
- Statuses: production, archived, staging

## Data Flow

```
seed.runner
  ├── ReferenceDataSeeder ──┐
  ├── IdentitySeeder ───────┤
  ├── MerchantSeeder ───────┤
  ├── AgentSeeder ──────────┼──→ Database (PostgreSQL)
  ├── DeviceSeeder ─────────┤
  ├── LocationSeeder ───────┤
  ├── TransactionSeeder ────┘
  ├── FraudRuleSeeder ──────┐
  └── ModelRegistrySeeder ──┘
```

## Reproducibility

All seeders use fixed Faker seed (42) for deterministic output.

To regenerate identical data:
```bash
python -m seed.runner --reset
```

## Performance

- Bulk inserts via SQLAlchemy `bulk_insert_batched`
- Batch size: 1000 records per flush
- 10,000 transactions: ~5-10 seconds
- 100,000 transactions: ~50-60 seconds
- 1,000,000+ transactions: scalable (increase batch size)

## Verification

After seeding, verify with:

```bash
# Count records
python -c "from seed.runner import SeedRunner; import asyncio; \
r = SeedRunner(); print(asyncio.run(r.get_stats()))"

# Or via psql
psql -c "SELECT COUNT(*) FROM transactions;"
psql -c "SELECT COUNT(*) FROM users;"
psql -c "SELECT COUNT(*) FROM merchants;"
```

## Adding New Seeders

1. Create `backend/seed/seeders/my_seeder.py`
2. Extend `BaseSeeder`
3. Implement `async def seed(self) -> dict[str, int]`
4. Add to `SEEDERS` list in `runner.py`

Example:
```python
from seed.base import BaseSeeder
from app.models.my_model import MyModel

class MySeeder(BaseSeeder):
    async def seed(self) -> dict[str, int]:
        records = [{"field": "value"}]
        await self.bulk_insert(MyModel, records)
        self.add_stat("my_records", len(records))
        return self.get_stats()

    async def clear(self):
        await self.clear_table("my_table")
```

## Troubleshooting

### Foreign Key Violations
Ensure seeders run in correct order. The `SEEDERS` list in `runner.py` defines dependency order.

### Duplicate Key Errors
Use `--reset` flag to truncate before seeding.

### Out of Memory
Reduce batch size in `BaseSeeder.__init__` or split into smaller runs.

## Next Steps

After seeding:
1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev` (from frontend/)
3. Login with: `admin@fraudwatch.com` / `FraudWatch@2024`
4. View dashboard with realistic data

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@fraudwatch.com | FraudWatch@2024 |
| Fraud Analyst | analyst@fraudwatch.com | FraudWatch@2024 |
| Compliance Officer | compliance@fraudwatch.com | FraudWatch@2024 |
| Risk Analyst | risk@fraudwatch.com | FraudWatch@2024 |
| Support | support@fraudwatch.com | FraudWatch@2024 |

All 30 demo customers use the same password: `FraudWatch@2024`