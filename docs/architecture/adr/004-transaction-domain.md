# Architecture Decision Record: Transaction Domain Design

**Status**: Accepted  
**Date**: 2024-01-15  
**Author**: Principal Software Architect  
**Domain**: Transaction Domain  

---

## Context

FraudWatch is an AI-powered financial fraud detection platform. The Transaction domain is the core of the system — it represents the financial transactions that are ingested from external payment systems and analyzed for fraud.

The Transaction domain must:
- Support 10M+ transactions per day
- Be partition-ready for time-series data
- Support multiple payment ecosystems (mobile money, banking, cards)
- Enable fraud detection through rich contextual data
- Maintain referential integrity for compliance
- Be extensible for future payment types

## Decision

### 1. Normalized Schema Design

**Decision**: Use a normalized schema with foreign key references to related entities rather than denormalizing into a single table.

**Rationale**:
- Merchants, agents, devices, and locations are shared across many transactions
- Normalization prevents data duplication and update anomalies
- Enables independent lifecycle management (e.g., deactivating a merchant)
- Supports referential integrity for compliance auditing

**Trade-off**: Slightly more complex queries with JOINs, but PostgreSQL handles this efficiently with proper indexing.

### 2. Reference Tables for Enumerated Values

**Decision**: Use database reference tables (currencies, payment_methods, transaction_types, transaction_statuses, risk_levels) rather than Python enums or hardcoded values.

**Rationale**:
- Enables runtime configuration without code changes
- Supports audit trail (status changes tracked via FK)
- Allows metadata per reference value (e.g., color codes for risk levels)
- Alembic migrations can seed reference data

**Trade-off**: Additional JOINs for status/type lookups, mitigated by selectin loading.

### 3. UUID Primary Keys

**Decision**: Use UUID v4 for all primary keys.

**Rationale**:
- Prevents ID enumeration attacks
- Enables offline ID generation
- Supports distributed systems and future sharding
- Consistent with Identity domain

**Trade-off**: Larger index size compared to integer IDs, but acceptable at 10M/day scale.

### 4. JSONB for Extensible Metadata

**Decision**: Use PostgreSQL JSONB for transaction metadata.

**Rationale**:
- Different payment systems have different fields
- Avoids schema changes for each new payment type
- Supports GIN indexing for querying metadata
- PostgreSQL JSONB is performant and supports indexing

**Trade-off**: Less type safety than structured columns, mitigated by Pydantic validation at the service layer.

### 5. selectin Lazy Loading

**Decision**: Use `lazy="selectin"` for all relationships.

**Rationale**:
- Eliminates N+1 query problem
- Single query per relationship level
- Predictable performance
- Good balance between eager and lazy loading

**Trade-off**: Slightly more memory usage than lazy="raise", but appropriate for this read-heavy domain.

### 6. Separate Entity for Transaction Status

**Decision**: Model transaction status as a separate reference table rather than a string column.

**Rationale**:
- Enables status lifecycle management
- Supports terminal status tracking
- Allows future status transitions to be data-driven
- Consistent with architecture document

**Trade-off**: Requires JOIN for status lookups, but status is always loaded with transactions.

### 7. Optional Foreign Keys for Contextual Entities

**Decision**: Make merchant_id, agent_id, device_id, location_id optional (nullable).

**Rationale**:
- Not all transactions have device or location data
- Mobile money transactions may not involve a merchant
- Agent-facilitated transactions are a subset
- NULL represents "unknown" rather than "not applicable"

**Trade-off**: Requires COALESCE or IS NULL checks in queries.

## Alternatives Considered

### Alternative 1: Single Denormalized Transaction Table

**Proposed**: Store all transaction data in a single table with JSONB for all variable fields.

**Rejected because**:
- Data duplication for merchants, agents, devices
- No referential integrity
- Difficult to update merchant information across transactions
- Compliance requirements demand referential integrity
- Query performance degrades with large JSONB blobs

### Alternative 2: Event Sourcing with Separate Event Store

**Proposed**: Store transactions as immutable events in an append-only log.

**Rejected because**:
- Over-engineered for current requirements
- Complex query patterns for analytics
- Higher storage costs
- Team unfamiliarity with event sourcing patterns
- Can be introduced later for specific use cases (investigation timeline)

## Consequences

### Advantages
1. **Referential Integrity**: All foreign keys ensure data consistency
2. **Extensibility**: JSONB metadata supports future payment types
3. **Performance**: Proper indexing supports 10M+ transactions/day
4. **Partitioning**: transaction_timestamp enables monthly partitioning
5. **Compliance**: Audit fields on all entities
6. **Maintainability**: Clear separation of concerns

### Trade-offs
1. **Query Complexity**: Normalized schema requires JOINs
2. **Index Size**: UUID PKs + multiple indexes increase storage
3. **Migration Complexity**: Reference tables need seed data

### Future Scalability
1. **Partitioning**: Ready for monthly range partitioning on transaction_timestamp
2. **Sharding**: UUID PKs support distributed sharding
3. **Read Replicas**: Analytics queries can be routed to replicas
4. **Archival**: Partition-based archival for data older than 90 days

### Potential Limitations
1. **JSONB Performance**: Heavy metadata queries may need GIN indexes
2. **Status History**: Current design only tracks current status; future state machine may be needed
3. **Multi-currency**: exchange_rate column supports basic multi-currency; complex FX may need separate table

## Related Decisions

- ADR-001: Base Model Design (UUID PKs, audit fields)
- ADR-002: Identity Domain Design (RBAC)
- ADR-003: Database Architecture (partitioning, indexing)

## References

- Architecture Document: `docs/architecture/database-architecture.md`
- Identity Domain: `docs/architecture/identity-domain-summary.md`