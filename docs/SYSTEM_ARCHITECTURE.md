# FraudWatch System Architecture

## Overview

FraudWatch is an enterprise AI-powered fraud detection and risk intelligence platform built with a modern microservices architecture.

## Backend Architecture

### Core Technologies
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Authentication**: JWT with RBAC
- **API Versioning**: /api/v1

### Service Layer
```
app/services/
├── explainability.py     # Prediction explanations
├── analytics.py          # Analytics queries
├── monitoring.py         # Model health/drift
├── search.py            # Global search
├── prediction.py        # Core prediction pipeline
├── fraud_alert.py       # Alert management
├── fraud_case.py        # Case management
├── fraud_rule.py        # Rule management
├── model_registry.py    # Model registry
├── transaction.py       # Transaction handling
├── merchant.py          # Merchant management
├── device.py            # Device management
├── location.py          # Location management
├── user.py              # User management
├── role.py              # Role management
├── permission.py        # Permission management
├── auth.py              # Authentication
├── session.py           # Session management
├── refresh_token.py     # Token refresh
└── jwt.py               # JWT utilities
```

### Repository Layer
All services use the repository pattern with async SQLAlchemy sessions.

### API Endpoints

#### Core Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/version` - API version

#### Prediction Explainability
- `GET /api/v1/predictions/{id}/explanation` - Full explanation
- `GET /api/v1/predictions/{id}/features` - Feature snapshot
- `GET /api/v1/predictions/{id}/rules` - Rule results
- `GET /api/v1/predictions/{id}/fallback` - Fallback explanation

#### Analytics
- `GET /api/v1/analytics/dashboard` - All analytics
- `GET /api/v1/analytics/fraud` - Fraud metrics
- `GET /api/v1/analytics/fraud/trends` - Fraud trends
- `GET /api/v1/analytics/fraud/merchant` - By merchant
- `GET /api/v1/analytics/fraud/device` - By device
- `GET /api/v1/analytics/operations` - Operations metrics
- `GET /api/v1/analytics/model` - Model metrics

#### Monitoring
- `GET /api/v1/monitoring/health` - System health
- `GET /api/v1/monitoring/model` - Model details
- `GET /api/v1/monitoring/model/stats` - Model statistics
- `GET /api/v1/monitoring/drift` - Drift indicators

#### Search
- `GET /api/v1/search?q=` - Global search
- `GET /api/v1/search/transactions` - Transaction search
- `GET /api/v1/search/predictions` - Prediction search
- `GET /api/v1/search/alerts` - Alert search
- `GET /api/v1/search/cases` - Case search

## Frontend Architecture

### Core Technologies
- **Framework**: Next.js 16.2.10
- **UI**: shadcn/ui + Tailwind CSS
- **State**: Zustand + TanStack Query
- **Charts**: Apache ECharts
- **Animations**: GSAP

### Animation Abstraction Layer
```
lib/animations/
├── index.ts                 # Barrel exports
├── prefers-reduced-motion.ts  # Accessibility utilities
├── cards.ts                # Card animations
├── sidebar.ts              # Sidebar animations
├── modal.ts                # Modal animations
├── page-transition.ts      # Page transitions
├── table.ts                # Table row animations
├── notifications.ts        # Notification animations
├── charts.ts               # Chart animations
└── stagger.ts              # Stagger utilities
```

### Chart Components
```
components/charts/
├── fraud-trend-chart.tsx        # Line chart with area
├── risk-distribution-chart.tsx    # Pie chart
├── model-performance-chart.tsx    # Performance line chart
├── latency-chart.tsx            # Bar chart
└── rule-frequency-chart.tsx     # Rule bar chart
```

### Routes Structure
```
app/
├── (dashboard)/
│   ├── dashboard/
│   │   ├── page.tsx              # Overview
│   │   ├── investigations/
│   │   ├── users/
│   │   ├── roles/
│   │   ├── merchants/
│   │   └── models/
│   ├── ml/
│   │   ├── overview/
│   │   ├── predictions/
│   │   ├── explainability/
│   │   ├── models/
│   │   ├── training/
│   │   ├── experiments/
│   │   ├── monitoring/
│   │   └── analytics/
│   └── audit/
├── login/
└── register/
```

## ML Pipeline Architecture

### Components
1. **Feature Engineering** (`ml/feature_engineering/`)
   - Transaction features
   - Customer features
   - Merchant features
   - Device features
   - Velocity features

2. **Rule Engine** (`ml/rules/`)
   - Base rule interface
   - Rule registry
   - Rule loader
   - Various rule implementations

3. **Model Registry** (`ml/models/`)
   - Base model interface
   - Model registry integration
   - Model loading

4. **Training** (`ml/training/`)
   - Dataset builder
   - Trainer
   - Evaluator

5. **Deployment** (`ml/deployment/`)
   - Deployment manager
   - Hot-swap loader

## Security

- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Session management
- Password hashing with bcrypt
- Rate limiting support

## Scalability

- Async-first architecture
- Database connection pooling
- Redis caching
- Celery for background tasks
- Horizontal scaling ready
