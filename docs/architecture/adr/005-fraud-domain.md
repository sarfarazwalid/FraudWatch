# Architecture Decision Record: Fraud Domain Design

**Status**: Accepted  
**Date**: 2024-01-15  
**Author**: Principal Software Architect  
**Domain**: Fraud Domain  

---

## Context

FraudWatch is an AI-powered financial fraud detection platform. The Fraud domain is responsible for the complete fraud investigation lifecycle - from detection through alerting, investigation, and resolution.

The Fraud domain must:
- Handle 100,000+ alerts per day
- Support real-time fraud detection and risk scoring
- Maintain complete audit trails for compliance
- Enable analyst collaboration on investigations
- Store immutable ML predictions and explanations
- Scale to millions of investigation records
- Support partition-ready time-series queries

## Decision

### 1. Separate Alert and Case Entities

**Decision**: Model FraudAlert and FraudCase as separate entities rather than combining them.

**Rationale**:
- **Separation of Concerns**: Alert is detection, Case is investigation
- **Different Lifecycles**: Alerts can exist without cases (dismissed, false positive)
- **Lightweight Alerts**: Alerts should be fast to generate without case overhead
- **Multiple Alerts to Case**: One case can consolidate multiple related alerts
- **Workflow Flexibility**: Alerts have triage workflow, cases have investigation workflow
- **Performance**: Alert queries remain lightweight without case relationships

**Trade-off**: Slightly more complex data model, but cleaner domain semantics justify this.

### 2. Separate Comments Entity

**Decision**: Store fraud comments in a separate FraudComment table rather than JSONB array on FraudCase.

**Rationale**:
- **Queryability**: Easy to query by author, date, visibility
- **Pagination**: Comments can be paginated efficiently
- **Edit History**: Support edit tracking without bloating case table
- **Visibility Control**: Can index on visibility for security queries
- **Compliance**: Immutable audit-ready tables
- **Analytics**: Enables analytics on comment patterns

**Trade-off**: Requires JOIN for case with comments, mitigated by selectin loading.

### 3. Separate Attachments Entity

**Decision**: Store only attachment metadata in FraudAttachment table, never binary files.

**Rationale**:
- **Database Performance**: Binary BLOBs slow queries and increase storage costs
- **Scalability**: Object storage (S3/GCS) handles large files efficiently
- **CDN Support**: Object storage integrates with CDNs for fast downloads
- **Lifecycle Management**: Different retention policies for metadata vs files
- **Backup Strategy**: File backups don't impact database backups
- **Cost**: Object storage is cheaper than database storage

**Trade-off**: Requires integration with object storage service.

### 4. Immutable Prediction Records

**Decision**: Never update Prediction records - each ML inference creates a new immutable record.

**Rationale**:
- **Audit Compliance**: Complete inference history for regulatory requirements
- **Model Monitoring**: Track prediction drift over time
- **Debugging**: Reproduce issues with exact inference context
- **Forensics**: Investigate why specific predictions were made
- **A/B Testing**: Compare predictions across model versions
- **Data Integrity**: Prevents accidental or malicious modification

**Trade-off**: Larger table size over time, requires partitioning strategy.

### 5. Append-Only InvestigationTimeline

**Decision**: InvestigationTimeline is append-only - never update or delete records.

**Rationale**:
- **Complete Audit Trail**: Regulatory requirement for fraud investigations
- **Forensic Analysis**: Reconstruct investigation sequence
- **Compliance**: AML/KYC regulations require immutable audit trails
- **Accountability**: Track every analyst action with timestamps
- **Dispute Resolution**: Investigate disputes with complete history

**Trade-off**: Table grows continuously, requires partitioning and archival strategy.

### 6. Model-Agnostic PredictionExplanation

**Decision**: Design PredictionExplanation to support multiple XAI techniques (SHAP, LIME, Feature Importance, etc.) without model-specific fields.

**Rationale**:
- **Future-Proofing**: New XAI techniques can be added without schema changes
- **Flexibility**: Different models may use different explanation methods
- **No Vendor Lock-in**: Not tied to SHAP or LIME libraries
- **Research Friendly**: Can experiment with new explanation techniques
- **Clean Abstraction**: Generic fields support all current and future methods

**Design**:
- `explanation_method`: Enum identifying technique used
- `feature_name`: Generic feature identifier
- `feature_value`: Feature value for this prediction
- `importance_score`: Generic importance metric
- `contribution_direction`: Positive/negative/none
- `display_order`: For UI rendering

**Trade-off**: Less optimized for specific techniques, but gains flexibility.

### 7. UUID Primary Keys

**Decision**: Use UUID v4 for all primary keys across fraud domain.

**Rationale**:
- **Consistency**: Matches Identity and Transaction domains
- **Security**: Prevents ID enumeration
- **Distributed Systems**: Enables multi-region deployment
- **No Central Sequence**: Avoids single point of failure

**Trade-off**: Larger index size, but acceptable at scale.

### 8. Soft Delete for All Models

**Decision**: Implement soft delete (deleted_at) for all fraud domain models.

**Rationale**:
- **Compliance**: Never lose audit trail data
- **Investigation Integrity**: Maintain referential integrity
- **Recovery**: Ability to restore accidentally deleted records
- **Legal Hold**: Support litigation holds

**Trade-off**: Additional IS NULL checks in queries, mitigated by view/helper.

## Case Workflow Design

### Finite State Machine

```
NEW → TRIAGED → UNDER_INVESTIGATION → ESCALATED → AWAITING_CUSTOMER → CONFIRMED_FRAUD → RESOLVED → CLOSED
```

**States**:
- **NEW**: Case created, awaiting initial review
- **TRIAGED**: Initial assessment complete
- **UNDER_INVESTIGATION**: Active investigation in progress
- **ESCALATED**: Escalated to senior analyst/compliance
- **AWAITING_CUSTOMER**: Waiting for customer response
- **CONFIRMED_FRAUD**: Fraud confirmed, proceeding with resolution
- **FALSE_POSITIVE**: Determined to be false positive
- **RESOLVED**: Investigation complete
- **CLOSED**: Case fully closed with all actions complete

**State Transitions**:
- Only valid transitions allowed (enforced by business logic, not database)
- Timeline records every state change with actor and timestamp
- Previous/new status stored for audit

## Database Constraints

### NOT NULL Strategy
- Primary keys (all auto-generated UUIDs)
- Business keys (alert_number, case_number)
- Foreign keys to required entities (transaction_id, case_id)
- Critical status fields (status, priority)
- Core content fields (comment, file_name, checksum)
- Audit fields (created_at on all models)

### Positive Score Constraints
- risk_score: 0-100
- confidence_score: 0-1
- probability_score: 0-1
- overall_risk_score: 0-100
- rule_score: 0-100
- ml_score: 0-1
- behavior_score: 0-100
- velocity_score: 0-100
- geolocation_score: 0-100
- device_score: 0-100
- importance_score: >= 0
- loss_amount: >= 0
- escalation_level: >= 0
- inference_time_ms: >= 0

## Index Strategy

### Single Indexes
- alert_number, case_number (unique business keys)
- transaction_id (FK, heavily queried)
- status, severity, priority, decision (filtering)
- assigned_analyst_id, investigator_id (user queries)
- generated_at, opened_at, assessed_at, prediction_timestamp (time-series)
- triggered_rule_id (rule analytics)
- model_version_id (ML monitoring)
- explanation_method, feature_name (explanation queries)

### Composite Indexes
- (status, severity): Alert queue optimization
- (assigned_analyst_id, status): Analyst workload queries
- (transaction_id, generated_at): Transaction alert history
- (case_id, status): Case status queries
- (transaction_id, prediction_timestamp): Prediction timeline
- (model_version_id, prediction_timestamp): Model monitoring
- (case_id, performed_at): Timeline retrieval
- (case_id, created_at): Comment history

## Alternatives Considered

### Alternative 1: Single Investigation Table

**Proposed**: Combine alert, case, and timeline into single investigation table with JSONB for variable data.

**Rejected because**:
- Violates normalization principles
- Query complexity for different workflows
- Difficult to enforce data integrity
- Complicates audit requirements
- Poor performance for large text fields (comments, attachments)
- No clear query patterns

### Alternative 2: Event Sourcing with EventStore

**Proposed**: Store all state changes as immutable events in an event store.

**Rejected because**:
- Over-engineered for current requirements
- Snapshot complexity for case state
- Higher learning curve and operational complexity
- Current schema already captures audit trail with InvestigationTimeline
- Can be introduced later for specific compliance needs

### Alternative 3: Hardcoded Enums Instead of Python Enum Classes

**Proposed**: Use string columns without Python enums, validate in business logic.

**Rejected because**:
- Database enums provide automatic validation
- Type safety at ORM layer
- Prevents invalid values at database level
- Self-documenting schema
- Alembic migrations track enum changes

## Consequences

### Advantages
1. **Separation of Concerns**: Each entity has clear responsibility
2. **Compliance Ready**: Immutable predictions and timelines meet regulatory requirements
3. **Performance**: Optimized indexes for common query patterns
4. **Extensibility**: Model-agnostic explanations support future ML models
5. **Maintainability**: Clean domain boundaries, single responsibility
6. **Scalability**: Partition-ready tables for growth
7. **Auditability**: Complete audit trail with Timeline and soft deletes

### Trade-offs
1. **Complexity**: More tables require more JOINs
2. **Storage**: Audit trail and immutability increase storage requirements
3. **Migration**: Extensive seed data for enums and reference tables
4. **Learning Curve**: Team needs to understand audit requirements

### Future Scalability
1. **Partitioning**: All time-series tables partition-ready (predictions, risk_assessments, alerts, cases)
2. **Sharding**: UUID keys support distributed sharding by transaction_id
3. **Read Replicas**: Analytics queries route to replicas
4. **Archival**: Old cases (>2 years) can archive to cold storage
5. **ML Pipeline**: PredictionExplanation supports new XAI techniques
6. **Multi-tenancy**: Schema supports multi-tenant with customer_id addition

### Potential Limitations
1. **Timeline Growth**: Append-only timeline requires partitioning strategy (monthly by case creation)
2. **Attachment Storage**: Requires S3/GCS integration
3. **Alert Volume**: 100K/day requires partitioning on generated_at
4. **Model Changes**: PredictionExplainations require re-running XAI if fields change

## Related Decisions

- ADR-001: Base Model Design (UUID PKs, audit fields, soft delete)
- ADR-002: Identity Domain Design (RBAC, user management)
- ADR-003: Database Architecture (partitioning, indexing)
- ADR-004: Transaction Domain Design (normalized schema, JSONB)
- ADR-005: Fraud Domain Design (this document)

## References

- Architecture Document: `docs/architecture/database-architecture.md`
- Transaction Domain: `docs/architecture/adr/004-transaction-domain.md`
- Identity Domain: `docs/architecture/identity-domain-summary.md`