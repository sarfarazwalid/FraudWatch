# FraudWatch Database Architecture Design Document

**Version**: 1.0.0  
**Date**: 2024-01-15  
**Author**: Principal Software Architect  
**Status**: Draft - Pending Review  
**Classification**: Internal - Confidential

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Domain Analysis](#2-business-domain-analysis)
3. [Entity Discovery](#3-entity-discovery)
4. [Entity Relationship Diagram](#4-entity-relationship-diagram)
5. [Table Design Specifications](#5-table-design-specifications)
6. [Base Model Design](#6-base-model-design)
7. [Identity & Access Control Domain](#7-identity--access-control-domain)
8. [Transaction Domain](#8-transaction-domain)
9. [Fraud Detection Domain](#9-fraud-detection-domain)
10. [Machine Learning Domain](#10-machine-learning-domain)
11. [System Configuration Domain](#11-system-configuration-domain)
12. [Index Strategy](#12-index-strategy)
13. [Database Constraints](#13-database-constraints)
14. [PostgreSQL Optimization](#14-postgreSQL-optimization)
15. [Security Design](#15-security-design)
16. [Implementation Roadmap](#16-implementation-roadmap)
17. [Risk Review](#17-risk-review)
18. [Assumptions & Future Recommendations](#18-assumptions--future-recommendations)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the complete database architecture for FraudWatch, an enterprise-grade AI-powered Financial Fraud Detection & Risk Intelligence Platform. The architecture is designed to support millions of transactions per day while maintaining sub-100ms query performance for critical fraud detection operations.

### 1.2 Design Principles

- **Scalability First**: Horizontal scaling support through sharding-ready design
- **Performance**: Optimized for high-throughput transaction processing
- **Auditability**: Complete audit trail for compliance (SOX, PCI-DSS, GDPR)
- **Explainability**: Full ML model explainability and prediction history
- **Flexibility**: Multi-tenancy ready without schema changes
- **Maintainability**: Clear separation of concerns, minimal technical debt

### 1.3 Technology Stack

- **Database**: PostgreSQL 16 (ACID compliance, JSON support, partitioning)
- **ORM**: SQLAlchemy 2.x (async support, type safety)
- **Connections**: pgBouncer (connection pooling at scale)
- **Caching**: Redis 7 (session store, query cache)

### 1.4 Scale Targets

- **Transactions**: 10M+ per day
- **Fraud Alerts**: 100K+ per day
- **Historical Data**: 10+ years retention
- **Concurrent Users**: 1,000+
- **Query Performance**: < 100ms for 95th percentile

---

## 2. Business Domain Analysis

### 2.1 Bounded Contexts

The FraudWatch platform is decomposed into the following bounded contexts, based on Domain-Driven Design principles:

```
┌─────────────────────────────────────────────────────────────┐
│                    FraudWatch Platform                       │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   Identity   │ Transaction  │   Fraud      │   Machine     │
│   Domain     │   Domain     │   Domain     │   Learning    │
├──────────────┼──────────────┼──────────────┼───────────────┤
│   Users      │ Transactions │    Alerts    │   Models      │
│   Roles      │   Merchants  │   Cases      │   Training    │
│   Permissions│   Payments   │             │   Predictions │
│   Sessions   │   Devices    │             │               │
└──────────────┴──────────────┴──────────────┴───────────────┘
      │              │              │               │
      └──────────────┴──────────────┴───────────────┘
                         │
                   System & Audit Domain
                   (Cross-cutting concerns)
```

### 2.2 Domain Details

#### **Identity Domain**
- **Purpose**: Manage user identities, authentication, and authorization
- **Responsibilities**: User lifecycle, role-based access control, session management
- **Boundaries**: Internal platform only, no customer data
- **Dependencies**: None (foundational)

#### **Transaction Domain**
- **Purpose**: Capture and track all financial transactions
- **Responsibilities**: Transaction ingestion, state management, merchant data
- **Boundaries**: Write-heavy, immutable except for status updates
- **Dependencies**: Identity (users), ML (fraud scoring)

#### **Fraud Domain**
- **Purpose**: Detect, alert, and investigate fraud
- **Responsibilities**: Alert generation, case management, investigation tracking
- **Boundaries**: Read-heavy for analytics, write-heavy for alerts
- **Dependencies**: Transaction, ML, Identity

#### **Machine Learning Domain**
- **Purpose**: Model lifecycle management and predictions
- **Responsibilities**: Model versioning, training history, predictions, explainability
- **Boundaries**: Write-once, read-many for predictions
- **Dependencies**: Transaction (features), Fraud (labels)

#### **System Domain**
- **Purpose**: Audit logging, notifications, configuration
- **Responsibilities**: Compliance, audit trails, system management
- **Boundaries**: Cross-cutting, write-heavy
- **Dependencies**: All other domains

---

## 3. Entity Discovery

### 3.1 Identity Domain Entities

| Entity | Business Purpose | Owner | Lifecycle | Expected Size | Growth Rate |
|--------|-----------------|-------|-----------|---------------|-------------|
| **User** | Platform users (analysts, admins) | Admin | Active/Inactive | < 1,000 | Low |
| **Role** | RBAC roles | Admin | Static + Custom | < 20 | Static |
| **Permission** | Granular permissions | Admin | Static | < 100 | Static |
| **RolePermission** | Role-Permission mapping | Admin | Static | < 500 | Static |
| **RefreshToken** | JWT refresh tokens | System | 7-day TTL | ~1,000 active | Low |
| **UserSession** | Active user sessions | System | 24-hour TTL | ~500 active | Low |

### 3.2 Transaction Domain Entities

| Entity | Business Purpose | Owner | Lifecycle | Expected Size | Growth Rate |
|--------|-----------------|-------|-----------|---------------|-------------|
| **Transaction** | Core transaction record | System | Immutable after 90 days | 10M+ | 10M/day |
| **Merchant** | Merchant/business data | Admin | Active/Inactive | < 100K | Low |
| **PaymentMethod** | Payment method types | System | Static | < 50 | Static |
| **Device** | Device fingerprints | System | 1-year retention | 10M+ | High |
| **Location** | Geographic data | System | 1-year retention | 10M+ | High |
| **Currency** | Supported currencies | Admin | Static | < 200 | Static |
| **TransactionType** | Credit/Debit/Refund | System | Static | < 20 | Static |
| **TransactionStatus** | Pending/Completed/Failed | System | Static | < 20 | Static |
| **RiskLevel** | Low/Medium/High/Critical | System | Static | < 20 | Static |

### 3.3 Fraud Domain Entities

| Entity | Business Purpose | Owner | Lifecycle | Expected Size | Growth Rate |
|--------|-----------------|-------|-----------|---------------|-------------|
| **FraudAlert** | Automated fraud alerts | ML System | Resolved/Archived | 100K/day | High |
| **FraudCase** | Manual investigation cases | Analyst | Open/Closed | 1M+ | Medium |
| **FraudRule** | Configurable fraud rules | Admin | Versioned | < 50 | Low |
| **InvestigationTimeline** | Case activity log | System | Immutable | 10M+ | Medium |
| **Prediction** | ML predictions | ML System | Immutable after 90 days | 10M+ | High |
| **PredictionExplanation** | SHAP explanations | ML System | Immutable after 90 days | 10M+ | High |

### 3.4 Machine Learning Domain Entities

| Entity | Business Purpose | Owner | Lifecycle | Expected Size | Growth Rate |
|--------|-----------------|-------|-----------|---------------|-------------|
| **ModelVersion** | ML model versions | ML Engineer | Active/Deprecated | < 100 | Low |
| **TrainingRun** | Model training runs | ML System | Immutable | < 1,000 | Low |
| **DatasetMetadata** | Training dataset info | ML Engineer | Immutable | < 500 | Low |
| **FeatureImportance** | Feature weights | ML System | Per model version | < 1,000 | Low |
| **ModelMetrics** | Model performance metrics | ML System | Per training run | < 5,000 | Low |
| **ModelRegistry** | Model artifact paths | ML Engineer | Versioned | < 100 | Low |

### 3.5 System Domain Entities

| Entity | Business Purpose | Owner | Lifecycle | Expected Size | Growth Rate |
|--------|-----------------|-------|-----------|---------------|-------------|
| **AuditLog** | Compliance audit trail | System | 7-year retention | 100M+ | Very High |
| **Notification** | User notifications | System | Read/Deleted | 10M+ | High |
| **NotificationTemplate** | Notification templates | Admin | Static | < 50 | Static |
| **SystemSetting** | Configuration values | Admin | Versioned | < 100 | Static |

---

## 4. Entity Relationship Diagram

### 4.1 High-Level ER Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        IDENTITY DOMAIN                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐      ┌──────────────┐      ┌─────────────┐   │
│  │    User    │◄────►│ Role         │◄────►│ Permission  │   │
│  └─────┬──────┘      └──────────────┘      └─────────────┘   │
│        │                                                         │
│   ┌────┴────┐                                                   │
│   │         │                                                   │
│   ▼         ▼                                                   │
│ ┌──────────┐  ┌──────────────┐                                  │
│ │ Refresh  │  │ UserSession  │                                  │
│ │ Token    │  └──────────────┘                                  │
│ └──────────┘                                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    │ FK: user_id
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                       TRANSACTION DOMAIN                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Transaction                                              │   │
│  │  - id (PK)                                               │   │
│  │  - user_id (FK → User)                                   │   │
│  │  - merchant_id (FK → Merchant)                           │   │
│  │  - payment_method_id (FK → PaymentMethod)                │   │
│  │  - device_id (FK → Device)                               │   │
│  │  - location_id (FK → Location)                           │   │
│  │  - amount, currency, status, risk_level                  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Merchant │  │  Device  │  │ Location │  │  Payment │       │
│  │          │  │          │  │          │  │  Method  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  Reference Tables:                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│  │ Currency   │ │ TxType     │ │ TxStatus   │ │ RiskLevel  │    │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    │ FK: transaction_id
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FRAUD DETECTION DOMAIN                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐          ┌────────────────┐                 │
│  │ FraudAlert     │◄────────►│  FraudCase     │                 │
│  │                │  1:1     │                │                 │
│  └───────┬────────┘          └────────────────┘                 │
│          │ 1                                               1..*   │
│          ▼                                                       │
│  ┌────────────────┐          ┌────────────────────┐             │
│  │ Prediction     │◄────────►│ PredictionExplanation│           │
│  │                │  1:1     │  (SHAP values)       │             │
│  └────────────────┘          └────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐          │
│  │ InvestigationTimeline                              │          │
│  │ (Case activity log)                                │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌────────────────┐                                             │
│  │   FraudRule    │                                             │
│  └────────────────┘                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    │ FK: model_version_id
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    MACHINE LEARNING DOMAIN                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐                     │
│  │ ModelVersion     │   │ ModelRegistry     │                     │
│  └────────┬─────────┘   └──────────────────┘                     │
│           │ 1            1..*                                    │
│           ▼              ┌──────────────────┐                     │
│  ┌──────────────────┐   │ FeatureImportance │                     │
│  │ TrainingRun      │   └──────────────────┘                     │
│  └────────┬─────────┘                                             │
│           │ 1         1..*                                      │
│           ▼              ┌──────────────────┐                     │
│  ┌──────────────────┐   │   ModelMetrics   │                      │
│  │ DatasetMetadata  │   └──────────────────┘                      │
│  └──────────────────┘                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

All domains reference:
┌──────────────────────────────────────────────────────────────────┐
│                        SYSTEM DOMAIN                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────┐   ┌──────────────┐ │
│  │ AuditLog                               │   │ Notification │ │
│  │ (entity_type, entity_id, action, ...)  │   │              │ │
│  └────────────────────────────────────────┘   └──────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────┐                     │
│  │ NotificationTemplate                   │                     │
│  └────────────────────────────────────────┘                     │
│                                                                  │
│  ┌────────────────────────────────────────┐                     │
│  │ SystemSetting                          │                     │
│  └────────────────────────────────────────┘                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Relationship Types

#### One-to-One (1:1)
- **FraudAlert ↔ FraudCase**: Each alert spawns at most one investigation case
- **Prediction ↔ PredictionExplanation**: Each prediction has one SHAP explanation
- **User ↔ UserSession**: One active session per user (simplification)

#### One-to-Many (1:N)
- **User → Transaction**: One user creates many transactions
- **Transaction → Prediction**: One transaction gets one prediction (current design)
- **FraudCase → InvestigationTimeline**: Case has many timeline events
- **ModelVersion → TrainingRun**: One model version has multiple training runs
- **TrainingRun → ModelMetrics**: One run has multiple metrics
- **User → Notification**: User receives many notifications

#### Many-to-Many (M:N)
- **User ↔ Permission**: Users have multiple permissions, permissions assigned to multiple roles
- **Role ↔ Permission**: Roles contain multiple permissions, permissions belong to multiple roles

#### Optional vs Required
- **Required**: `user_id` in Transaction (every transaction has a user)
- **Optional**: `device_id` in Transaction (not all transactions have device data)
- **Optional**: `location_id` in Transaction (IP geolocation may fail)

---

## 5. Table Design Specifications

### 5.1 Base Model Pattern

All tables inherit from a base model providing:

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `id` | UUID | Primary key | Random UUID v4, not sequential |
| `created_at` | TIMESTAMPTZ | Creation timestamp | Set by database |
| `updated_at` | TIMESTAMPTZ | Modification timestamp | Updated by trigger |
| `deleted_at` | TIMESTAMPTZ | Soft delete | NULL = active, else deleted |
| `created_by` | UUID | Creator reference | FK to users.id |
| `updated_by` | UUID | Updater reference | FK to users.id |
| `version` | INTEGER | Row version | Optimistic locking |

**Rationale for Base Model**:
- **UUID**: Prevents ID enumeration, enables offline ID generation
- **Timestamps**: Audit trail, TTL calculations, age-based partitioning
- **Soft Delete**: Compliance requirement, data retention, auditability
- **Created/Updated By**: Accountability, GDPR right-to-erasure tracking
- **Version**: Optimistic concurrency control for high-contention tables

### 5.2 Reference Tables (Static Data)

Reference tables contain static or semi-static data loaded at startup:

```yaml
Currency:
  - id, code (ISO 4217), name, symbol, decimal_places
  
TransactionType:
  - id, code (credit/debit/refund/transfer), description
  
TransactionStatus:
  - id, code (pending/processing/completed/failed/flagged), 
    description, is_terminal
  
RiskLevel:
  - id, code (low/medium/high/critical), 
    score_range (JSON: {min, max}), color_code
    
PaymentMethod:
  - id, code (card/bank_transfer/wallet/...), 
    name, is_supported
```

---

## 6. Identity & Access Control Domain

### 6.1 Tables

#### **users**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - email: VARCHAR(255) [UNIQUE, NOT NULL]
  - email_verified: BOOLEAN [DEFAULT: false]
  - password_hash: VARCHAR(255) [NOT NULL]
  - first_name: VARCHAR(100) [NOT NULL]
  - last_name: VARCHAR(100) [NOT NULL]
  - role_id: UUID [FK → roles.id, NOT NULL]
  - organization: VARCHAR(255) [NULLABLE]
  - is_active: BOOLEAN [DEFAULT: true]
  - last_login: TIMESTAMPTZ [NULLABLE]
  - failed_login_attempts: INTEGER [DEFAULT: 0]
  - locked_until: TIMESTAMPTZ [NULLABLE]

Optional Fields:
  - phone: VARCHAR(20)
  - avatar_url: TEXT
  - preferences: JSONB [DEFAULT: '{}']
  - metadata: JSONB [DEFAULT: '{}']

Constraints:
  - email format validation
  - password complexity (enforced at app level)
  - UNIQUE(email)
  
Indexes:
  - email (UNIQUE, BTREE)
  - role_id (BTREE)
  - is_active (BTREE)
  - organization (BTREE, partial WHERE is_active = true)

Expected Record Count: < 1,000
Growth Rate: Low (linear with organization size)
```

**Lifecycle**: Users are created by admins, deactivated on termination, never deleted (compliance).

#### **roles**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - name: VARCHAR(50) [UNIQUE, NOT NULL]
  - description: TEXT [NOT NULL]
  - is_system_role: BOOLEAN [DEFAULT: false]
  - is_active: BOOLEAN [DEFAULT: true]

Optional Fields:
  - metadata: JSONB [DEFAULT: '{}']

Constraints:
  - name format: ^[a-z_]+$ (snake_case)
  - UNIQUE(name)

Indexes:
  - name (UNIQUE, BTREE)

Expected Record Count: < 20 (5-10 system roles)
Growth Rate: Static
```

**System Roles**:
- `super_admin`: Full system access
- `admin`: Organizational admin
- `fraud_analyst`: Investigation and review
- `compliance_officer`: Audit and reporting
- `viewer`: Read-only access

#### **permissions**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - resource: VARCHAR(100) [NOT NULL]
  - action: VARCHAR(50) [NOT NULL]
  - description: TEXT [NOT NULL]

Constraints:
  - UNIQUE(resource, action)
  - resource format: ^[a-z_]+$
  - action format: ^(create|read|update|delete|execute)$

Indexes:
  - (resource, action) (UNIQUE, BTREE)

Expected Record Count: < 100
Growth Rate: Low (adds 5-10 per feature)

Sample Permissions:
  - (transactions, read)
  - (transactions, update)
  - (fraud_alerts, create)
  - (fraud_alerts, read)
  - (fraud_cases, update)
  - (models, execute)
  - (reports, read)
```

#### **role_permissions** (M:N Junction)
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - role_id: UUID [FK → roles.id, NOT NULL]
  - permission_id: UUID [FK → permissions.id, NOT NULL]

Constraints:
  - UNIQUE(role_id, permission_id)
  - CASCADE delete on role/permission change

Indexes:
  - role_id (BTREE)
  - permission_id (BTREE)
  - (role_id, permission_id) (UNIQUE, BTREE)

Expected Record Count: < 500
Growth Rate: Low
```

#### **refresh_tokens**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - user_id: UUID [FK → users.id, NOT NULL]
  - token_hash: VARCHAR(255) [UNIQUE, NOT NULL]
  - expires_at: TIMESTAMPTZ [NOT NULL]
  - revoked: BOOLEAN [DEFAULT: false]

Optional Fields:
  - device_info: JSONB
  - ip_address: INET

Constraints:
  - expires_at > created_at
  - UNIQUE(token_hash)

Indexes:
  - user_id (BTREE)
  - token_hash (UNIQUE, BTREE)
  - expires_at (BTREE, partial WHERE revoked = false)
  - (user_id, revoked) (BTREE)

Lifecycle:
  - TTL: 7 days
  - Cleanup: Daily batch job
  - Revocation on logout/password change

Expected Record Count: ~1,000 active
Growth Rate: Low
```

#### **user_sessions**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - user_id: UUID [FK → users.id, NOT NULL]
  - session_token: VARCHAR(255) [UNIQUE, NOT NULL]
  - expires_at: TIMESTAMPTZ [NOT NULL]
  - ip_address: INET [NOT NULL]
  - user_agent: TEXT [NOT NULL]

Optional Fields:
  - device_info: JSONB

Constraints:
  - expires_at > created_at
  - UNIQUE(session_token)

Indexes:
  - user_id (BTREE)
  - session_token (UNIQUE, BTREE)
  - expires_at (BTREE, partial WHERE expires_at > NOW())
  
Lifecycle:
  - TTL: 24 hours
  - Refresh on activity
  - Cleanup: Hourly batch job

Expected Record Count: ~500 active
Growth Rate: Low
```

---

## 7. Transaction Domain

### 7.1 Core Transaction Table

#### **transactions**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - transaction_id: VARCHAR(100) [UNIQUE, NOT NULL]
  - user_id: UUID [FK → users.id, NOT NULL]
  - merchant_id: UUID [FK → merchants.id, NOT NULL]
  - payment_method_id: UUID [FK → payment_methods.id, NOT NULL]
  - currency_id: UUID [FK → currencies.id, NOT NULL]
  - type_id: UUID [FK → transaction_types.id, NOT NULL]
  - status_id: UUID [FK → transaction_statuses.id, NOT NULL]
  - amount: NUMERIC(18,2) [NOT NULL]
  - fee_amount: NUMERIC(18,2) [NOT NULL]
  - tax_amount: NUMERIC(18,2) [DEFAULT: 0]
  - net_amount: NUMERIC(18,2) [NOT NULL]
  - payment_date: TIMESTAMPTZ [NOT NULL]
  - risk_level_id: UUID [FK → risk_levels.id, NULLABLE]
  - fraud_score: NUMERIC(5,4) [NULLABLE, range: 0.0-1.0]

Optional Fields:
  - device_id: UUID [FK → devices.id, NULLABLE]
  - location_id: UUID [FK → locations.id, NULLABLE]
  - reference_number: VARCHAR(100)
  - description: TEXT
  - metadata: JSONB [DEFAULT: '{}']
  - tags: TEXT[] [DEFAULT: '{}']

Constraints:
  - amount > 0
  - net_amount = amount - fee_amount - tax_amount
  - fraud_score BETWEEN 0 AND 1
  - UNIQUE(transaction_id)

Indexes:
  - transaction_id (UNIQUE, BTREE)
  - user_id (BTREE)
  - merchant_id (BTREE)
  - payment_date (BRIN) - high cardinality, time-series
  - (user_id, payment_date) (BTREE) - user transaction history
  - (merchant_id, payment_date) (BTREE) - merchant analytics
  - status_id (BTREE, partial WHERE status_id IN ('pending', 'flagged'))
  - risk_level_id (BTREE, partial WHERE risk_level_id IS NOT NULL)
  - created_at (BRIN) - partitioning support

Expected Record Count: 10M+ per month, 120M+ per year
Growth Rate: 10M/day (peak)
```

**Design Notes**:
- **Payment Date**: Actual transaction time (immutable)
- **Status**: Pending → Processing → Completed/Failed/Flagged
- **Risk Level**: Assigned by ML model
- **Fraud Score**: 0.0 (safe) to 1.0 (definite fraud)
- **BRIN Index**: Perfect for time-series data, low overhead

### 7.2 Reference Tables (Transaction)

#### **merchants**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - merchant_id: VARCHAR(100) [UNIQUE, NOT NULL]
  - name: VARCHAR(255) [NOT NULL]
  - category: VARCHAR(100) [NOT NULL]
  - country_code: CHAR(2) [NOT NULL]
  - is_active: BOOLEAN [DEFAULT: true]

Optional Fields:
  - registration_number: VARCHAR(100)
  - tax_id: VARCHAR(100)
  - address: JSONB
  - contact_email: VARCHAR(255)
  - contact_phone: VARCHAR(20)
  - metadata: JSONB

Constraints:
  - UNIQUE(merchant_id)
  - country_code format: ISO 3166-1 alpha-2

Indexes:
  - merchant_id (UNIQUE, BTREE)
  - category (BTREE)
  - country_code (BTREE)
  - is_active (BTREE, partial WHERE is_active = true)

Expected Record Count: < 100K
Growth Rate: Low (onboarding driven)
```

#### **devices**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - fingerprint: VARCHAR(255) [UNIQUE, NOT NULL]
  - device_type: VARCHAR(50) [NOT NULL]
  - os: VARCHAR(50) [NOT NULL]
  - browser: VARCHAR(50) [NULLABLE]

Optional Fields:
  - user_agent_hash: VARCHAR(64)
  - screen_resolution: VARCHAR(20)
  - timezone: VARCHAR(50)
  - language: VARCHAR(10)
  - metadata: JSONB

Constraints:
  - UNIQUE(fingerprint)
  - device_type: mobile/tablet/desktop

Indexes:
  - fingerprint (UNIQUE, BTREE)
  - device_type (BTREE)

Lifecycle:
  - Retention: 1 year from last seen
  - Partitioned by created_at

Expected Record Count: 10M+
Growth Rate: High
```

#### **locations**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - ip_address: INET [NOT NULL]
  - country_code: CHAR(2) [NOT NULL]
  - city: VARCHAR(100) [NOT NULL]

Optional Fields:
  - region: VARCHAR(100)
  - postal_code: VARCHAR(20)
  - latitude: NUMERIC(10,8)
  - longitude: NUMERIC(11,8)
  - timezone: VARCHAR(50)
  - is_vpn: BOOLEAN [DEFAULT: false]
  - is_proxy: BOOLEAN [DEFAULT: false]
  - is_tor: BOOLEAN [DEFAULT: false]
  - risk_score: NUMERIC(5,4)

Constraints:
  - country_code: ISO 3166-1 alpha-2
  - latitude BETWEEN -90 AND 90
  - longitude BETWEEN -180 AND 180

Indexes:
  - ip_address (BTREE)
  - country_code (BTREE)
  - (ip_address, country_code) (UNIQUE, BTREE)

Lifecycle:
  - Retention: 1 year
  - Deduplication on IP

Expected Record Count: 10M+ unique IPs
Growth Rate: High
```

#### **payment_methods**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - code: VARCHAR(50) [UNIQUE, NOT NULL]
  - name: VARCHAR(100) [NOT NULL]
  - category: VARCHAR(50) [NOT NULL]
  - is_supported: BOOLEAN [DEFAULT: true]

Optional Fields:
  - icon_url: TEXT
  - metadata: JSONB

Constraints:
  - UNIQUE(code)
  - category: card/wallet/bank_transfer/crypto/other

Indexes:
  - code (UNIQUE, BTREE)

Expected Record Count: < 50
Growth Rate: Static
```

#### **transaction_types**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - code: VARCHAR(20) [UNIQUE, NOT NULL]
  - name: VARCHAR(100) [NOT NULL]
  - description: TEXT

Constraints:
  - UNIQUE(code)
  - code: credit/debit/refund/transfer/reversal

Expected Record Count: < 20
Growth Rate: Static
```

#### **transaction_statuses**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - code: VARCHAR(20) [UNIQUE, NOT NULL]
  - name: VARCHAR(100) [NOT NULL]
  - description: TEXT
  - is_terminal: BOOLEAN [NOT NULL]
  - sort_order: INTEGER [NOT NULL]

Constraints:
  - UNIQUE(code)
  - sort_order > 0
  - is_terminal: completed/failed/cancelled/refunded

Indexes:
  - code (UNIQUE, BTREE)
  - sort_order (BTREE)

Sample Data:
  - pending (1, false)
  - processing (2, false)
  - completed (3, true)
  - failed (4, true)
  - flagged (5, false)

Expected Record Count: < 20
Growth Rate: Static
```

#### **risk_levels**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - code: VARCHAR(20) [UNIQUE, NOT NULL]
  - name: VARCHAR(100) [NOT NULL]
  - description: TEXT
  - score_min: NUMERIC(5,4) [NOT NULL]
  - score_max: NUMERIC(5,4) [NOT NULL]
  - color_hex: CHAR(7) [NOT NULL]
  - sort_order: INTEGER [NOT NULL]

Constraints:
  - UNIQUE(code)
  - score_min < score_max
  - score_min BETWEEN 0 AND 1
  - score_max BETWEEN 0 AND 1

Indexes:
  - code (UNIQUE, BTREE)
  - sort_order (BTREE)

Sample Data:
  - low (0.00-0.30, #00FF00)
  - medium (0.30-0.50, #FFFF00)
  - high (0.50-0.80, #FFA500)
  - critical (0.80-1.00, #FF0000)

Expected Record Count: < 10
Growth Rate: Static
```

#### **currencies**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - code: CHAR(3) [UNIQUE, NOT NULL]
  - name: VARCHAR(100) [NOT NULL]
  - symbol: VARCHAR(10) [NOT NULL]
  - decimal_places: INTEGER [NOT NULL]

Constraints:
  - UNIQUE(code)
  - code: ISO 4217
  - decimal_places BETWEEN 0 AND 4

Indexes:
  - code (UNIQUE, BTREE)

Expected Record Count: < 200
Growth Rate: Static
```

---

## 8. Fraud Detection Domain

### 8.1 Core Tables

#### **fraud_alerts**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - transaction_id: UUID [FK → transactions.id, NOT NULL]
  - rule_id: UUID [FK → fraud_rules.id, NULLABLE]
  - type: VARCHAR(100) [NOT NULL]
  - severity: VARCHAR(20) [NOT NULL]
  - score: NUMERIC(5,4) [NOT NULL]
  - threshold: NUMERIC(5,4) [NOT NULL]
  - description: TEXT [NOT NULL]
  - status: VARCHAR(20) [NOT NULL, DEFAULT: 'open']
  - created_by: VARCHAR(100) [NOT NULL]

Optional Fields:
  - metadata: JSONB [DEFAULT: '{}']
  - tags: TEXT[] [DEFAULT: '{}']

Constraints:
  - severity: info/warning/error/critical
  - status: open/acknowledged/resolved/dismissed
  - score BETWEEN 0 AND 1

Indexes:
  - transaction_id (BTREE)
  - rule_id (BTREE, partial WHERE rule_id IS NOT NULL)
  - (status, severity, created_at) (BTREE) - alert dashboard
  - severity (BTREE)
  - created_at (BRIN)
  - (transaction_id, status) (UNIQUE, BTREE) - prevent duplicate alerts

Expected Record Count: 100K/day, 36.5M/year
Growth Rate: Very High
Partitioning: Monthly by created_at
```

**Design Notes**:
- Auto-created by ML or rule engine
- Each transaction can have multiple alerts
- Unique constraint prevents duplicate processing

#### **fraud_cases**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - case_number: VARCHAR(50) [UNIQUE, NOT NULL]
  - title: VARCHAR(255) [NOT NULL]
  - description: TEXT [NOT NULL]
  - status: VARCHAR(20) [NOT NULL, DEFAULT: 'open']
  - priority: VARCHAR(20) [NOT NULL]
  - assigned_to: UUID [FK → users.id, NULLABLE]
  - created_by: UUID [FK → users.id, NOT NULL]

Optional Fields:
  - loss_amount: NUMERIC(18,2)
  - recovered_amount: NUMERIC(18,2)
  - resolution_notes: TEXT
  - metadata: JSONB [DEFAULT: '{}']
  - tags: TEXT[] [DEFAULT: '{}']

Constraints:
  - status: open/in_progress/closed/archived
  - priority: low/medium/high/critical
  - UNIQUE(case_number)

Indexes:
  - case_number (UNIQUE, BTREE)
  - status (BTREE)
  - priority (BTREE)
  - assigned_to (BTREE)
  - created_at (BRIN)
  - (status, priority) (BTREE) - case management dashboard

Expected Record Count: 1M+
Growth Rate: Medium
Lifecycle: Open → In Progress → Closed → Archived (7 years)
```

**Design Notes**:
- One alert may spawn one case (1:1, but not enforced for flexibility)
- Cases are manually managed by fraud analysts
- Immutable after closure (compliance)

#### **fraud_rules**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - name: VARCHAR(100) [UNIQUE, NOT NULL]
  - description: TEXT [NOT NULL]
  - type: VARCHAR(50) [NOT NULL]
  - condition: JSONB [NOT NULL]
  - severity: VARCHAR(20) [NOT NULL]
  - threshold: NUMERIC(5,4) [NOT NULL]
  - is_active: BOOLEAN [DEFAULT: true]
  - version: INTEGER [NOT NULL, DEFAULT: 1]
  - created_by: UUID [FK → users.id, NOT NULL]

Optional Fields:
  - metadata: JSONB [DEFAULT: '{}']

Constraints:
  - type: ml/rule/business
  - severity: info/warning/error/critical

Indexes:
  - name (UNIQUE, BTREE)
  - is_active (BTREE, partial WHERE is_active = true)
  - version (BTREE)

Expected Record Count: < 100
Growth Rate: Static
```

#### **investigation_timeline**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - case_id: UUID [FK → fraud_cases.id, NOT NULL]
  - action: VARCHAR(100) [NOT NULL]
  - performed_by: UUID [FK → users.id, NOT NULL]
  - notes: TEXT

Optional Fields:
  - old_value: JSONB
  - new_value: JSONB
  - metadata: JSONB

Constraints:
  - All fields required except metadata
  - Immutable after insert

Indexes:
  - case_id (BTREE)
  - (case_id, created_at) (BTREE) - timeline retrieval
  - performed_by (BTREE)

Expected Record Count: 10M+
Growth Rate: Medium
```

#### **predictions**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - transaction_id: UUID [FK → transactions.id, UNIQUE, NOT NULL]
  - model_version_id: UUID [FK → model_versions.id, NOT NULL]
  - score: NUMERIC(5,4) [NOT NULL]
  - risk_level_id: UUID [FK → risk_levels.id, NOT NULL]
  - predicted_at: TIMESTAMPTZ [NOT NULL]

Optional Fields:
  - metadata: JSONB [DEFAULT: '{}']

Constraints:
  - score BETWEEN 0 AND 1
  - UNIQUE(transaction_id)

Indexes:
  - transaction_id (UNIQUE, BTREE)
  - model_version_id (BTREE)
  - risk_level_id (BTREE)
  - predicted_at (BRIN)

Expected Record Count: 10M+ per year
Growth Rate: High
Partitioning: Monthly by predicted_at
```

**Design Notes**:
- One prediction per transaction (current design)
- Immutable after creation
- Link to SHAP explanation

#### **prediction_explanations**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - prediction_id: UUID [FK → predictions.id, UNIQUE, NOT NULL]
  - features: JSONB [NOT NULL]  # {"feature_name": value, ...}
  - shap_values: JSONB [NOT NULL]  # {"feature_name": shap_value, ...}
  - base_value: NUMERIC(10,6) [NOT NULL]

Optional Fields:
  - metadata: JSONB [DEFAULT: '{}']

Constraints:
  - UNIQUE(prediction_id)

Indexes:
  - prediction_id (UNIQUE, BTREE)

Expected Record Count: 10M+ per year
Growth Rate: High
Partitioning: Monthly by prediction_id's created_at
```

---

## 9. Machine Learning Domain

### 9.1 Model Management

#### **model_versions**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - model_name: VARCHAR(100) [NOT NULL]
  - version: VARCHAR(50) [NOT NULL]
  - algorithm: VARCHAR(50) [NOT NULL]
  - status: VARCHAR(20) [NOT NULL]
  - artifact_path: TEXT [NOT NULL]
  - created_by: UUID [FK → users.id, NOT NULL]

Optional Fields:
  - description: TEXT
  - training_run_id: UUID [FK → training_runs.id]
  - metadata: JSONB

Constraints:
  - status: development/staging/production/archived
  - UNIQUE(model_name, version)

Indexes:
  - (model_name, status) (BTREE)
  - status (BTREE, partial WHERE status = 'production')

Expected Record Count: < 100
Growth Rate: Low
```

#### **training_runs**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - model_version_id: UUID [FK → model_versions.id, NOT NULL]
  - dataset_id: UUID [FK → dataset_metadata.id, NOT NULL]
  - started_at: TIMESTAMPTZ [NOT NULL]
  - completed_at: TIMESTAMPTZ [NULLABLE]
  - status: VARCHAR(20) [NOT NULL]
  - parameters: JSONB [NOT NULL]

Optional Fields:
  - metrics: JSONB
  - artifacts_path: TEXT
  - logs_path: TEXT
  - error_message: TEXT
  - metadata: JSONB

Constraints:
  - status: running/completed/failed
  - completed_at > started_at

Indexes:
  - model_version_id (BTREE)
  - dataset_id (BTREE)
  - started_at (BRIN)

Expected Record Count: < 1,000
Growth Rate: Low
```

#### **dataset_metadata**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - name: VARCHAR(255) [NOT NULL]
  - version: VARCHAR(50) [NOT NULL]
  - format: VARCHAR(20) [NOT NULL]
  - size_bytes: BIGINT [NOT NULL]
  - row_count: INTEGER [NOT NULL]
  - feature_count: INTEGER [NOT NULL]
  - created_by: UUID [FK → users.id, NOT NULL]

Optional Fields:
  - description: TEXT
  - source: VARCHAR(255)
  - schema: JSONB
  - metadata: JSONB

Constraints:
  - UNIQUE(name, version)

Indexes:
  - (name, version) (UNIQUE, BTREE)

Expected Record Count: < 500
Growth Rate: Low
```

#### **feature_importance**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - model_version_id: UUID [FK → model_versions.id, NOT NULL]
  - feature_name: VARCHAR(100) [NOT NULL]
  - importance_score: NUMERIC(10,6) [NOT NULL]
  - rank: INTEGER [NOT NULL]

Constraints:
  - UNIQUE(model_version_id, feature_name)
  - rank > 0

Indexes:
  - model_version_id (BTREE)
  - importance_score (BTREE) - top features

Expected Record Count: < 1,000
Growth Rate: Low
```

#### **model_metrics**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - training_run_id: UUID [FK → training_runs.id, NOT NULL]
  - metric_name: VARCHAR(100) [NOT NULL]
  - metric_value: NUMERIC(15,6) [NOT NULL]
  - dataset_split: VARCHAR(20) [NOT NULL]

Constraints:
  - dataset_split: train/validation/test
  - UNIQUE(training_run_id, metric_name, dataset_split)

Indexes:
  - training_run_id (BTREE)

Expected Record Count: < 5,000
Growth Rate: Low
```

#### **model_registry**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - model_version_id: UUID [FK → model_versions.id, NOT NULL]
  - artifact_type: VARCHAR(50) [NOT NULL]
  - storage_path: TEXT [NOT NULL]
  - checksum: VARCHAR(64) [NOT NULL]
  - size_bytes: BIGINT [NOT NULL]

Constraints:
  - artifact_type: model/scaler/encoder/pipeline
  - checksum: SHA-256

Indexes:
  - model_version_id (BTREE)
  - artifact_type (BTREE)

Expected Record Count: < 500
Growth Rate: Low
```

---

## 10. System Domain

### 10.1 Audit Logging

#### **audit_logs**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - actor_id: UUID [FK → users.id, NOT NULL]
  - entity_type: VARCHAR(100) [NOT NULL]
  - entity_id: UUID [NOT NULL]
  - action: VARCHAR(50) [NOT NULL]
  - old_value: JSONB [NULLABLE]
  - new_value: JSONB [NULLABLE]
  - ip_address: INET [NOT NULL]
  - user_agent: TEXT [NOT NULL]

Optional Fields:
  - correlation_id: UUID
  - metadata: JSONB

Constraints:
  - All actions logged: CREATE/UPDATE/DELETE/LOGIN/LOGOUT/VIEW
  - Immutable after insert

Indexes:
  - (entity_type, entity_id) (BTREE)
  - actor_id (BTREE)
  - action (BTREE)
  - created_at (BRIN)
  - (entity_type, action, created_at) (BTREE) - audit queries
  - GIN index on metadata (JSONB)

Expected Record Count: 100M+ per year
Growth Rate: Very High
Partitioning: Monthly by created_at
Retention: 7 years (compliance)
Archival: After 2 years to cold storage
```

**Design Notes**:
- Write-once, append-only
- Never updated or deleted
- Automated archival to object storage

### 10.2 Notifications

#### **notifications**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - user_id: UUID [FK → users.id, NOT NULL]
  - type: VARCHAR(50) [NOT NULL]
  - channel: VARCHAR(20) [NOT NULL]
  - subject: VARCHAR(255) [NOT NULL]
  - body: TEXT [NOT NULL]
  - status: VARCHAR(20) [NOT NULL, DEFAULT: 'pending']

Optional Fields:
  - template_id: UUID [FK → notification_templates.id]
  - data: JSONB
  - read_at: TIMESTAMPTZ
  - sent_at: TIMESTAMPTZ

Constraints:
  - channel: email/sms/in_app
  - status: pending/sent/delivered/failed/read

Indexes:
  - user_id (BTREE)
  - status (BTREE)
  - (user_id, created_at) (BTREE) - user notification feed
  - created_at (BRIN)

Expected Record Count: 10M+ per year
Growth Rate: High
Partitioning: Monthly by created_at
```

#### **notification_templates**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - name: VARCHAR(100) [UNIQUE, NOT NULL]
  - type: VARCHAR(50) [NOT NULL]
  - channel: VARCHAR(20) [NOT NULL]
  - subject_template: VARCHAR(255) [NOT NULL]
  - body_template: TEXT [NOT NULL]
  - is_active: BOOLEAN [DEFAULT: true]

Optional Fields:
  - variables: JSONB [DEFAULT: '{}']

Constraints:
  - UNIQUE(name)
  - channel: email/sms/in_app

Indexes:
  - name (UNIQUE, BTREE)
  - (type, is_active) (BTREE)

Expected Record Count: < 50
Growth Rate: Static
```

### 10.3 System Configuration

#### **system_settings**
```yaml
Primary Key:
  - id: UUID

Required Fields:
  - key: VARCHAR(100) [UNIQUE, NOT NULL]
  - value: JSONB [NOT NULL]
  - type: VARCHAR(20) [NOT NULL]
  - is_sensitive: BOOLEAN [DEFAULT: false]

Optional Fields:
  - description: TEXT
  - updated_by: UUID [FK → users.id]

Constraints:
  - type: string/number/boolean/json
  - UNIQUE(key)

Indexes:
  - key (UNIQUE, BTREE)

Expected Record Count: < 100
Growth Rate: Static

Sensitive Settings (encrypted):
  - jwt_secret_key
  - encryption_key
  - api_keys
```

---

## 11. Index Strategy

### 11.1 Index Recommendations

#### Primary Indexes
- **UUID Primary Keys**: All tables use UUIDv4 as PK
- **Unique Business Keys**: Separate UNIQUE constraints on business identifiers (email, transaction_id, etc.)

#### Composite Indexes
```sql
-- Transaction History by User
CREATE INDEX idx_transactions_user_date 
ON transactions(user_id, payment_date DESC);

-- Dashboard: Open Alerts by Severity
CREATE INDEX idx_alerts_dashboard 
ON fraud_alerts(status, severity, created_at DESC) 
WHERE status = 'open';

-- Case Management: Assigned Cases by Priority
CREATE INDEX idx_cases_assignment 
ON fraud_cases(assigned_to, priority, created_at DESC) 
WHERE status != 'closed';

-- Audit Trail: Entity History
CREATE INDEX idx_audit_entity 
ON audit_logs(entity_type, entity_id, created_at DESC);

-- User Notifications: Recent First
CREATE INDEX idx_notifications_user 
ON notifications(user_id, created_at DESC);
```

#### Partial Indexes
```sql
-- Active Users Only
CREATE INDEX idx_users_active 
ON users(email) WHERE is_active = true;

-- Active Fraud Rules
CREATE INDEX idx_rules_active 
ON fraud_rules(name) WHERE is_active = true;

-- Non-Revoked Tokens
CREATE INDEX idx_refresh_tokens_valid 
ON refresh_tokens(token_hash) WHERE revoked = false AND expires_at > NOW();

-- Open Alerts
CREATE INDEX idx_alerts_open 
ON fraud_alerts(created_at DESC) WHERE status = 'open';
```

#### Covering Indexes (Include Columns)
```sql
-- Transaction Dashboard (avoid table lookup)
CREATE INDEX idx_transactions_dashboard 
ON transactions(user_id, payment_date DESC) 
INCLUDE (amount, status_id, risk_level_id);

-- User Profile Access
CREATE INDEX idx_users_profile 
ON users(email) 
INCLUDE (first_name, last_name, role_id, organization);
```

#### BRIN Indexes (Time-Series)
```sql
-- Transactions (append-only, time-ordered)
CREATE INDEX idx_transactions_created_brin 
ON transactions USING BRIN(created_at) 
WITH (pages_per_range = 32);

-- Audit Logs (massive table, time-series)
CREATE INDEX idx_audit_created_brin 
ON audit_logs USING BRIN(created_at) 
WITH (pages_per_range = 64);
```

### 11.2 Index Strategy Rationale

- **BRIN for Time-Series**: 10-100x smaller than BTREE, perfect for append-only data
- **Partial Indexes**: Reduce index size, speed up maintenance
- **Composite Indexes**: Match common query patterns (user + date)
- **Covering Indexes**: Eliminate table lookups for hot paths

---

## 12. Database Constraints

### 12.1 Check Constraints

```sql
-- Transaction amount validation
ALTER TABLE transactions 
ADD CONSTRAINT chk_amount_positive 
CHECK (amount > 0);

-- Fraud score range
ALTER TABLE predictions 
ADD CONSTRAINT chk_fraud_score_range 
CHECK (fraud_score BETWEEN 0 AND 1);

-- Email format
ALTER TABLE users 
ADD CONSTRAINT chk_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Risk level boundary
ALTER TABLE risk_levels 
ADD CONSTRAINT chk_risk_levels 
CHECK (score_min >= 0 AND score_max <= 1 AND score_min < score_max);

-- Latitude/Longitude
ALTER TABLE locations 
ADD CONSTRAINT chk_latitude 
CHECK (latitude BETWEEN -90 AND 90);

ALTER TABLE locations 
ADD CONSTRAINT chk_longitude 
CHECK (longitude BETWEEN -180 AND 180);

-- Active timestamps
ALTER TABLE audit_logs 
ADD CONSTRAINT chk_timestamp_order 
CHECK (created_at <= now());
```

### 12.2 Foreign Key Constraints

```sql
-- Transaction → User (required)
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;

-- Transaction → Merchant (required)
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_merchant 
FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE RESTRICT;

-- Transaction → Device (optional)
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_device 
FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL;

-- Alert → Transaction (required)
ALTER TABLE fraud_alerts 
ADD CONSTRAINT fk_alerts_transaction 
FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE;

-- Case Timeline → Case (required)
ALTER TABLE investigation_timeline 
ADD CONSTRAINT fk_timeline_case 
FOREIGN KEY (case_id) REFERENCES fraud_cases(id) ON DELETE CASCADE;

-- Prediction → Transaction (required, unique)
ALTER TABLE predictions 
ADD CONSTRAINT fk_predictions_transaction 
FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE;
```

### 12.3 Unique Constraints

```sql
-- Business identifier uniqueness
CREATE UNIQUE INDEX uk_users_email ON users(email);
CREATE UNIQUE INDEX uk_merchants_id ON merchants(merchant_id);
CREATE UNIQUE INDEX uk_transactions_id ON transactions(transaction_id);
CREATE UNIQUE INDEX uk_fraud_cases_number ON fraud_cases(case_number);
CREATE UNIQUE INDEX uk_prediction_transaction ON predictions(transaction_id);
```

---

## 13. PostgreSQL Optimization

### 13.1 Partitioning Strategy

```sql
-- Transactions by month (range partitioning)
CREATE TABLE transactions (
    id UUID,
    payment_date TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (payment_date);

-- Create partitions
CREATE TABLE transactions_2024_01 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
-- Audit logs by month
CREATE TABLE audit_logs (
    id UUID,
    created_at TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (created_at);
```

**Partitioning Rules**:
- **Transactions**: Monthly partitions, retension after 7 years
- **Predictions**: Monthly partitions, retention after 2 years
- **Audit Logs**: Monthly partitions, archive after 2 years
- **Notifications**: Monthly partitions, delete after 1 year

### 13.2 Archival Strategy

```yaml
Active Data (Hot):
  - Transactions: Last 90 days
  - Alerts: Last 1 year
  - Audit Logs: Last 2 years
  - Predictions: Last 2 years

Cold Storage (S3/Azure Blob):
  - Transactions > 90 days
  - Predictions > 2 years
  - Audit Logs > 2 years

Deletion:
  - Notifications > 1 year
  - Soft-deleted records > 7 years
```

### 13.3 Index Maintenance

```sql
-- Reindex strategy
REINDEX INDEX CONCURRENTLY idx_transactions_created_brin;
ANALYZE transactions;

-- Vacuum settings for high-churn tables
ALTER TABLE audit_logs SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);
```

### 13.4 Connection Pooling

```yaml
pgBouncer Configuration:
  - max_connections: 200 (database)
  - default_pool_size: 20 (backend)
  - min_pool_size: 10
  - pool_mode: transaction
  - idle_in_transaction_session_timeout: 30s

Application Pooling:
  - SQLAlchemy pool_size: 20
  - SQLAlchemy max_overflow: 10
  - SQLAlchemy pool_recycle: 1800
  - SQLAlchemy pool_pre_ping: true
```

### 13.5 Future Read Replicas

```yaml
Primary:
  - Read/Write
  - All tables

Replica 1 (Analytics):
  - Read-only
  - Transactions, Predictions, Metrics

Replica 2 (Reporting):
  - Read-only
  - Audit Logs, Notifications
```

---

## 14. Security Design

### 14.1 Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users see only their transactions
CREATE POLICY user_transactions ON transactions
    FOR SELECT
    USING (user_id = current_user_id());

-- Policy: Analysts see their assigned cases
CREATE POLICY analyst_cases ON fraud_cases
    FOR SELECT
    USING (assigned_to = current_user_id() OR created_by = current_user_id());
```

### 14.2 Column-Level Encryption

```sql
-- Encrypted columns (using pgcrypto)
ALTER TABLE users 
ALTER COLUMN email TYPE ENCRYPTED;

ALTER TABLE system_settings 
ALTER COLUMN value TYPE ENCRYPTED 
WHERE key LIKE '%.secret' OR key LIKE '*.key';
```

### 14.3 Audit Logging Triggers

```sql
-- Automatic audit on critical tables
CREATE TRIGGER audit_fraud_cases
    AFTER INSERT OR UPDATE OR DELETE ON fraud_cases
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 14.4 Least Privilege

```yaml
Application User:
  - SELECT/INSERT/UPDATE on all tables
  - No DDL permissions
  - No SUPERUSER

Read Replica User:
  - SELECT only
  - No DML

Backup User:
  - pg_read_all_data
  - No write permissions
```

### 14.5 Data Masking

```sql
-- Mask PII in non-production
CREATE FUNCTION mask_email(email TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN regexp_replace(email, '^(.)(.*)(@.*)$', '\1***\3');
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

---

## 15. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **Base Model**: Create BaseModel with audit fields
2. **Enums**: Define all enums as PostgreSQL ENUM types or lookup tables
3. **Reference Tables**: Currency, TransactionType, TransactionStatus, RiskLevel, PaymentMethod
4. **Identity Domain**: Users, Roles, Permissions, RolePermissions
5. **Migrations**: Generate initial Alembic migration

### Phase 2: Transaction Ecosystem (Week 3-4)
1. **Transaction Tables**: Merchants, Devices, Locations
2. **Core Transaction**: transactions table with all foreign keys
3. **Indexes**: Implement all indexes from Section 11
4. **Migrations**: Generate and test migration
5. **Connection Pooling**: Configure pgBouncer

### Phase 3: Fraud Detection (Week 5-6)
1. **Prediction Tables**: predictions, prediction_explanations
2. **Alert Tables**: fraud_alerts with partitioning
3. **Case Management**: fraud_cases, investigation_timeline
4. **Rules Engine**: fraud_rules table
5. **Partitioning**: Set up partition management

### Phase 4: ML Integration (Week 7-8)
1. **Model Management**: model_versions, model_registry
2. **Training Metadata**: training_runs, dataset_metadata
3. **Explainability**: feature_importance, model_metrics
4. **Archival Strategy**: Implement data lifecycle policies

### Phase 5: System & Audit (Week 9)
1. **Audit Tables**: audit_logs with partitioning
2. **Notifications**: notifications, notification_templates
3. **System Config**: system_settings
4. **Audit Triggers**: Implement on all critical tables
5. **RLS Policies**: Enable on sensitive tables

### Phase 6: Testing & Optimization (Week 10)
1. **Load Testing**: Simulate 10M transactions
2. **Performance Tuning**: Analyze slow queries, add missing indexes
3. **Security Audit**: Review permissions, RLS policies
4. **Documentation**: Finalize ER diagrams, data dictionary
5. **Backup Strategy**: Configure pg_dump, PITR

---

## 16. Risk Review

### 16.1 Potential Bottlenecks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Transaction Table Growth** | High | Partition by month, archive after 90 days, read replicas |
| **Audit Log Volume** | Critical | BRIN indexes, monthly partitions, cold storage after 2 years |
| **UUID Sequential Reads** | Medium | UUIDv4 is random; consider UUIDv7 for better clustering |
| **JSONB Query Performance** | Medium | GIN indexes, avoid JSONB as PK, limit size |
| **Connection Saturation** | High | pgBouncer, connection pooling, request queueing |

### 16.2 Circular Dependencies

**Risk**: Identity domain is foundational, but audit_logs reference all domains.

**Mitigation**: 
- Use deferrable foreign keys for circular references
- Audit logs store entity_type and entity_id (no FK constraints)

### 16.3 Future Scaling Issues

**Issue**: Single database may become bottleneck at 100M+ transactions.

**Mitigation**:
- Design for sharding from day one (include `tenant_id`)
- Use logical replication for read replicas
- Partitioning enables per-partition migration

### 16.4 Normalization vs Performance

**Trade-off**: Over-normalization creates excessive joins.

**Resolution**:
- Denormalize high-cardinality reference data (currencies, risk_levels)
- Keep foreign keys (normalized) for entities with low cardinality
- Use JSONB for semi-structured metadata

### 16.5 Security Concerns

| Concern | Mitigation |
|----------|-----------|
| **PII Exposure** | Column-level encryption, RLS, audit logging |
| **SQL Injection** | Parameterized queries (ORM), input validation |
| **Data Breach** | Encryption at rest, row-level security, audit trail |
| **Privilege Escalation** | Least privilege, RBAC, separation of duties |

### 16.6 Technical Debt Risks

| Risk | Prevention |
|------|------------|
| **Schema Drift** | Alembic migrations, code review |
| **Unused Indexes** | Regular index review, `pg_stat_user_indexes` |
| **Table Bloat** | VACUUM, partitioning, archival |
| **Query Regression** | Query performance monitoring, EXPLAIN ANALYZE |

---

## 17. Assumptions & Future Recommendations

### 17.1 Assumptions

1. **Multi-tenancy Not Required Initially**: Schema is designed with future `tenant_id` support
2. **Single Region**: No geo-distribution in v1, but partitioning supports it
3. **PostgreSQL 16+**: Some features (BRIN, partitioning) require PG 11+
4. **10M Transactions/Day**: Estimated from mid-size payment processor
5. **7-Year Retention**: Based on financial compliance requirements

### 17.2 Future Recommendations

#### Short-term (Q2 2024)
- Implement database role separation (read/write/backup)
- Add query performance monitoring (pg_stat_statements)
- Set up automated failover (Patroni)

#### Medium-term (Q3 2024)
- Implement read replicas for reporting
- Add materialized views for dashboards
- Consider Citus for horizontal sharding

#### Long-term (Q4 2024+)
- Evaluate TimescaleDB for time-series optimization
- Implement database-level change data capture (CDC)
- Consider event sourcing for fraud investigations

---

## Appendix

### A. Data Dictionary Reference

See accompanying `data-dictionary.md` for detailed field descriptions.

### B. ER Diagram Notation

- **PK**: Primary Key
- **FK**: Foreign Key
- **1**: One
- **N**: Many
- **Optional**: Circle notation
- **Required**: Straight line

### C. Database User Roles

```yaml
postgres:
  - Superuser
  - Owner of all tables

fraudwatch_app:
  - Application user
  - SELECT/INSERT/UPDATE

fraudwatch_readonly:
  - Read replica user
  - SELECT only

fraudwatch_backup:
  - Backup user
  - pg_read_all_data

fraudwatch_migration:
  - Migration user
  - DDL permissions only
```

---

**Document Approval**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Principal Architect | [Name] | [Date] | |
| Lead Backend Engineer | [Name] | [Date] | |
| DBA | [Name] | [Date] | |
| Security Architect | [Name] | [Date] | |

**Revision History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-01-15 | [Architect] | Initial blueprint |
| | | | |
</parameter>
<parameter=task_progress>
- [x] Create root project structure
- [x] Initialize frontend (Next.js + TypeScript + Tailwind)
- [x] Initialize backend (FastAPI + SQLAlchemy)
- [x] Set up ML folder structure
- [x] Create Docker configuration
- [x] Configure environment variables
- [x] Prepare security architecture
- [x] Create documentation and Git files
- [x] Set up CI/CD pipelines
- [x] Set up code quality tools
- [x] Verify complete project structure
- [x] Design complete database architecture
</parameter>
</write_to_file>