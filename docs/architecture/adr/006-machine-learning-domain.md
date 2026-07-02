# ADR-006: Machine Learning Domain Architecture

## Status

**Accepted** - Phase 6 Implementation

## Context

FraudWatch requires a comprehensive MLOps persistence layer to support the enterprise AI-powered fraud detection platform. The ML domain must track model versions, training runs, datasets, metrics, predictions, and production deployments while maintaining reproducibility, auditability, and explainability.

### Problem Statement

- No existing structure for managing ML model lifecycle
- Need to support multiple ML frameworks (scikit-learn, TensorFlow, PyTorch, etc.)
- Requirement for complete lineage tracking from datasets to predictions
- Compliance requirements demand immutable audit trails
- Production deployment management needs rollback capabilities
- Model interpretability requires feature importance tracking

## Decision

We will implement a dedicated `app/models/ml/` domain with seven entities:

1. **DatasetMetadata** - Dataset lineage and integrity tracking
2. **TrainingRun** - Training execution metadata
3. **ModelVersion** - Immutable model version records
4. **ModelMetrics** - Evaluation metrics storage
5. **FeatureImportance** - Global feature importance scores
6. **PredictionHistory** - Immutable prediction audit trail
7. **ModelRegistry** - Production model lifecycle management

## Alternatives Considered

### Alternative 1: Single Unified Registry

**Approach**: Store all ML artifacts (models, runs, metrics) in a single table with JSONB columns.

**Pros**:
- Simpler schema
- Flexibility to store arbitrary metadata

**Cons**:
- Difficult to query and index specific attributes
- No data integrity constraints
- Poor performance for common queries
- Hard to maintain referential integrity
- Not MLOps best practice

**Decision**: Rejected - lack of structure and constraints makes it unsuitable for enterprise MLOps.

### Alternative 2: External MLOps Platform Integration

**Approach**: Use external platforms like MLflow, Weights & Biases, or Neptune for ML tracking.

**Pros**:
- Purpose-built for ML workflows
- Rich UI and visualization
- Proven in production

**Cons**:
- External dependency
- Data residency concerns
- Additional infrastructure cost
- Integration complexity
- Less control over schema and constraints

**Decision**: Rejected - We need native integration with our database for compliance and auditability. External tools can be integrated later through APIs.

### Alternative 3: Hybrid Approach (Database + Object Storage)

**Approach**: Store metadata in database, large artifacts in S3/MinIO, link via paths.

**Pros**:
- Scalable artifact storage
- Industry standard pattern
- Cost effective

**Cons**:
- More complex architecture
- Requires artifact lifecycle management
- Additional failure points

**Decision**: Partially Accepted - We will use this hybrid approach. Model artifacts stored in object storage with paths/checksums in database. This is reflected in our ModelVersion schema (artifact_path, checksum).

## Consequences

### Positive

1. **Complete Lineage**: Full traceability from dataset → training run → model version → prediction
2. **Immutability**: Critical records (model versions, predictions) are never modified, ensuring audit compliance
3. **Reproducibility**: Git commits, random seeds, and dataset hashes enable exact reproduction
4. **Scalability**: Separate tables allow independent scaling and partitioning (e.g., prediction_history can be time-partitioned)
5. **MLOps Best Practices**: Follows industry standards for model registry and metadata tracking
6. **Explainability**: Feature importance storage supports model transparency requirements
7. **Production Safety**: Registry enables zero-downtime deployments and instant rollback

### Negative

1. **Schema Complexity**: 7 tables with relationships increase cognitive load
2. **Migration Overhead**: More migrations to manage as requirements evolve
3. **Query Complexity**: Multi-entity queries required for common operations
4. **Storage Growth**: Immutable prediction history grows continuously, requires archival strategy

### Neutral

1. **Framework Support**: Enum-based algorithm/framework tracking supports MLOps needs but requires updates for new frameworks
2. **Model Agnostic**: Design supports any model type but doesn't enforce specific interfaces

## Architectural Decisions

### 1. Why Model Versions Are Immutable

**Decision**: ModelVersion records are never updated after creation. New versions are created for any change.

**Rationale**:
- Reproducibility: Exact model artifact can be reproduced from version record
- Audit Trail: Complete history of all model iterations
- Compliance: Regulatory requirements often mandate version immutability
- SCD Type 2: Enables point-in-time analysis ("which model was in production on date X?")
- Debugging: Can trace issues to specific model versions

**Trade-offs**: Requires more storage but enables critical MLOps capabilities.

### 2. Why Training Runs Are Tracked Separately

**Decision**: TrainingRun is a distinct entity linked to DatasetMetadata and ModelVersion.

**Rationale**:
- Multiple Models: One training run can produce multiple model versions (e.g., hyperparameter search)
- Multiple Runs: One dataset can be used in many training runs
- Failed Runs: Not all training runs produce models (failures must be tracked)
- Resource Tracking: Duration, compute, and cost tracking per run
- Reproducibility: Training context (seed, commit, hyperparameters) preserved

**Trade-offs**: Additional join required to get model + training context, but enables critical lineage tracking.

### 3. Why Metrics Are Normalized

**Decision**: ModelMetrics uses standardized column names (accuracy, precision, recall, f1_score, roc_auc, log_loss).

**Rationale**:
- Schema Enforcement: Database ensures metric names and types are consistent
- Query Performance: Indexed columns enable fast metric-based filtering
- Data Integrity: CHECK constraints ensure valid ranges (0-1 for most metrics)
- Aggregation: Easy to compute average metrics across model versions
- Comparison: Standard metrics enable apples-to-apples comparison

**Trade-offs**: Less flexible than JSONB for arbitrary metrics, but consistency outweighs flexibility needs.

### 4. Why Prediction History Is Permanent

**Decision**: PredictionHistory records are immutable and never deleted (soft delete only).

**Rationale**:
- Compliance: Regulatory requirements (PCI DSS, GDPR) mandate audit trails
- Model Monitoring: Prediction distributions enable drift detection
- Debugging: Can trace why a specific prediction was made
- Legal Protection: Protects against liability claims
- Audit: External auditors require proof of inference history

**Trade-offs**: Storage grows indefinitely. Mitigation: Implement time-based archival (e.g., 90 days hot, older cold storage).

### 5. Why a Registry Exists

**Decision**: ModelRegistry provides a single source of truth for production models.

**Rationale**:
- Deployment Management: Quick lookup of "which model is in production?"
- Rollback Support: Previous version tracked for instant rollback
- Environment Awareness: Separate registry per environment (dev, staging, prod)
- Single Source of Truth: Avoids querying ModelVersion.deployed flags (which could be inconsistent)
- Audit Trail: deployment_notes and deployed_by tracked

**Trade-offs**: Denormalization (version tracked in both ModelVersion and ModelRegistry) but provides clarity and performance.

### 6. Unique Model Version Constraint

**Decision**: ModelVersion enforces uniqueness on (model_name, version), not globally unique versions.

**Rationale**:
- Natural Semantics: fraud_detection_v1 and phishing_detection_v1 can coexist
- Independent Evolution: Models can be versioned independently
- Deployment Clarity: Registry would be ambiguous if versions were global

**Implementation**: Application-level enforcement (repositories/services) ensures version increments per model_name.

## Relationships

```
DatasetMetadata (1) ←→ (N) TrainingRun (1) ←→ (N) ModelVersion (1) ←→ (1) ModelMetrics
                                                      (1) ←→ (N) FeatureImportance
                                                      (1) ←→ (N) PredictionHistory
                                                            
ModelRegistry (1) → (1) ModelVersion (current_model_version)
```

**Cardinality**:
- DatasetMetadata 1:N TrainingRun
- TrainingRun 1:N ModelVersion
- ModelVersion 1:1 ModelMetrics
- ModelVersion 1:N FeatureImportance
- ModelVersion 1:N PredictionHistory
- ModelVersion N:1 Transaction (via PredictionHistory)
- ModelRegistry 1:1 ModelVersion (via composite key model_name + version)

## Indexes Strategy

### model_versions
- `model_name` + `version` (composite unique - implicit via table design)
- `status` - Filter by model status (draft, production, archived)
- `training_run_id` - Join optimization
- `deployed` - Filter deployed models

### training_runs
- `dataset_id` - All runs for a dataset
- `training_status` - Filter by status
- `started_at` - Time-range queries

### dataset_metadata
- `dataset_name` (unique) - Lookup by name
- `source` - Filter by source type
- `hash` (unique) - Integrity verification

### prediction_history
- `transaction_id` + `prediction_timestamp` - All predictions for a transaction
- `model_version_id` + `prediction_timestamp` - All predictions by a model
- `prediction_timestamp` - Time-range queries for monitoring

### model_metrics
- `model_version_id` (unique) - One metrics record per version
- `evaluation_timestamp` - Time-series analysis

### model_registry
- `model_name` (unique) - One registry entry per model
- `deployment_environment` - Filter by environment
- `active` - Quick lookup of active models

## Constraints

### CHECK Constraints
1. `duration_seconds >= 0` - Training duration can't be negative
2. `latency_ms >= 0` - Prediction latency can't be negative
3. `ranking > 0` - Feature importance ranking must be positive
4. `accuracy, precision, recall, f1_score, roc_auc, fpr, fnr BETWEEN 0 AND 1` - All 0-1 metrics validated

### Foreign Key Constraints
- CASCADE deletes for ModelMetrics, FeatureImportance (deleting a model version removes dependent records)
- RESTRICT for PredictionHistory (prevents deletion of model versions with prediction history)

## Technology Stack

- **ORM**: SQLAlchemy 2.x with async support
- **Database**: PostgreSQL 15+ (ENUM support, CHECK constraints)
- **Schema Management**: Alembic
- **Migrations**: Version-controlled, reversible

## Future Support for Multiple ML Frameworks

### Framework Extension Points

1. **AlgorithmType Enum**: Easily extensible with new algorithm types
2. **FrameworkType Enum**: New frameworks added as values
3. **Hyperparameters (JSONB)**: Framework-agnostic hyperparameter storage
4. **Artifact Path**: Flexible storage path supports any serialization format

### Planned Enhancements

1. **Model Artifact Registry**: Integration with MLflow Model Registry
2. **Experiment Tracking**: Experiment table linking training runs to hyperparameter sets
3. **Model Signatures**: Input/output schema tracking for model validation
4. **Serving Metadata**: Model server, endpoint, and version tracking
5. **A/B Testing**: Shadow deployment and traffic splitting support

### Framework-Agnostic Design Patterns

```python
# Model version is framework-agnostic
class ModelVersion(Base):
    algorithm: AlgorithmType  # Enum
    framework: FrameworkType   # Enum
    artifact_path: str         # Works for any framework
    hyperparameters: str       # JSON, framework-agnostic
```

### Adding New Framework Support

1. Add value to `FrameworkType` enum
2. No schema changes required
3. Add framework-specific artifact handling in services layer
4. Update documentation

## Implementation Notes

### SQLAlchemy 2.x Compliance

- Uses `Mapped[]` type hints for all columns
- Uses `mapped_column()` for all column definitions
- Relationships use explicit `back_populates`
- `selectin` loading strategy for N+1 prevention
- No legacy `deferred()` or `undefer()`

### Decimal Precision

- Metrics (accuracy, precision, etc.): Numeric(5,4) allows 0.0000 to 1.0000
- Feature importance: Numeric(10,8) allows high precision
- Log loss: Numeric(10,6) allows values > 1

### Partitioning Strategy (Future)

PredictionHistory table will benefit from time-based partitioning:
```sql
-- Future PostgreSQL partitioning
CREATE TABLE prediction_history_2024_01 PARTITION OF prediction_history
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Performance Considerations

- UUID primary keys use `gen_random_uuid()` (PostgreSQL)
- Indexes on all foreign keys
- Composite indexes for common query patterns
- CHECK constraints validated at database level

## Testing Strategy

1. **Model Instantiation**: Verify all models can be created with valid data
2. **Relationship Integrity**: Verify bidirectional relationships work
3. **Constraint Enforcement**: Verify CHECK constraints reject invalid data
4. **Cascade Deletes**: Verify proper cascade behavior
5. **Unique Constraints**: Verify uniqueness enforcement
6. **Enum Validation**: Verify only valid enum values accepted
7. **Alembic Compatibility**: Verify migrations generate correctly

## References

- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [AWS SageMaker Model Registry](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)
- [Google Cloud AI Platform Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry)
- [MLOps Best Practices](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-production)

## Review History

| Date       | Reviewer | Status    | Notes |
|------------|----------|-----------|-------|
| 2026-01-20 | Arch Team | Accepted  | Approved for implementation |
| 2026-01-25 | DBA      | Approved  | Schema design validated |

## Appendix: Entity Summary

| Entity              | Lines of Code | Tables | Indexes | Constraints |
|-----|---------------|--------|---------|-------------|
| DatasetMetadata     | 95           | 1      | 4       | 2 (unique)  |
| TrainingRun         | 142          | 1      | 4       | 1 CHECK     |
| ModelVersion        | 135          | 1      | 6       | 0           |
| ModelMetrics        | 165          | 1      | 2       | 7 CHECK     |
| FeatureImportance   | 125          | 1      | 3       | 2 CHECK     |
| PredictionHistory   | 145          | 1      | 4       | 1 CHECK     |
| ModelRegistry       | 123          | 1      | 3       | 0           |
| **Total**           | **930**      | **7**  | **26**  | **13**      |

---

**Decision**: Implement dedicated ML domain with 7 entities, following MLOps best practices and ensuring reproducibility, auditability, and explainability.