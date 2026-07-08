# Deployment Guide

## Overview

This guide covers deploying FraudWatch to production environments.

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.12+
- Node.js 18+

## Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/fraudwatch
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generate-secure-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env)
```bash
NEXT_PUBLIC_API_URL=/api/v1
NEXT_PUBLIC_APP_NAME=FraudWatch
```

## Docker Deployment

```bash
# Build and start services
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python -m seed.runner
```

## Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

## Health Checks

- Backend: `GET /api/v1/health`
- Database: Check PostgreSQL connection
- Redis: Check cache connectivity

## Monitoring

- Prometheus metrics at `/metrics`
- Logs via structured logging
- Model drift alerts via webhook

## Scaling

- Backend: Horizontal pod autoscaling
- Workers: Scale based on queue depth
- Frontend: Static export or serverless
