# API Reference

## Overview

FraudWatch API v1 - Enterprise AI Fraud Operations Center

Base URL: `/api/v1`

## Authentication

All endpoints require JWT authentication via Bearer token.

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

## Core Endpoints

### Health Check
```
GET /api/v1/health
```

### Prediction Explainability
```
GET /api/v1/predictions/{id}/explanation
GET /api/v1/predictions/{id}/features
GET /api/v1/predictions/{id}/rules
GET /api/v1/predictions/{id}/fallback
```

### Analytics
```
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/fraud
GET /api/v1/analytics/fraud/trends
GET /api/v1/analytics/fraud/merchant
GET /api/v1/analytics/fraud/device
GET /api/v1/analytics/fraud/payment-method
GET /api/v1/analytics/fraud/transaction-type
GET /api/v1/analytics/operations
GET /api/v1/analytics/model
```

### Model Monitoring
```
GET /api/v1/monitoring/health
GET /api/v1/monitoring/model
GET /api/v1/monitoring/model/stats
GET /api/v1/monitoring/drift
```

### Search
```
GET /api/v1/search?q={query}&limit={limit}
GET /api/v1/search/transactions?q={query}
GET /api/v1/search/predictions?q={query}
GET /api/v1/search/alerts?q={query}
GET /api/v1/search/cases?q={query}
```

## Response Format

All responses follow a consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
