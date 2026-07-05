# Celery Background Processing Architecture

## Overview

Transform FraudWatch from synchronous to event-driven fraud detection using Celery + Redis.

---

## Architecture Design

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                              │
│  POST /transactions → Store → Publish Event → 200 OK        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Message Broker (Redis)                     │
│  Queues:                                                     │
│  • fraud_prediction_queue   (high priority)                  │
│  • model_training_queue     (medium priority)                │
│  • alert_generation_queue  (high priority)                  │
│  • analytics_queue          (low priority)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Workers                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Worker Pool (concurrent)                              │   │
│  │  • predict_transaction_task                           │   │
│  │  • generate_fraud_alert_task                          │   │
│  │  • train_model_task                                   │   │
│  │  • update_dashboard_metrics_task                     │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Task Execution Flow                        │
│                                                              │
│  1. Load Transaction                                         │
│  2. Extract Features (Feature Engineering Engine)            │
│  3. Run Rule Engine (24 rules)                               │
│  4. Load ML Model (Model Registry)                           │
│  5. Run Inference                                            │
│  6. Combine Scores                                           │
│  7. Store Prediction                                         │
│  8. Generate Alert (if risk > 0.7)                           │
│  9. Update Analytics                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Queue Strategy

### Queue Definitions

```python
QUEUES = {
    "fraud_prediction_queue": {
        "priority": 1,  # Highest
        "concurrency": 8,
        "tasks": [
            "predict_transaction_task",
            "batch_predict_task",
        ]
    },
    "alert_generation_queue": {
        "priority": 2,
        "concurrency": 4,
        "tasks": [
            "generate_fraud_alert_task",
            "escalate_alert_task",
        ]
    },
    "model_training_queue": {
        "priority": 3,
        "concurrency": 2,
        "tasks": [
            "train_model_task",
            "evaluate_model_task",
            "deploy_model_task",
            "rollback_model_task",
        ]
    },
    "analytics_queue": {
        "priority": 4,  # Lowest
        "concurrency": 2,
        "tasks": [
            "update_dashboard_metrics_task",
            "compute_fraud_trends_task",
            "update_risk_statistics_task",
        ]
    },
}
```

### Routing Strategy

- **Immediate routing**: High-risk transactions (>0.8) → alert_generation_queue
- **Batch routing**: Bulk predictions → fraud_prediction_queue
- **Scheduled routing**: Model training → model_training_queue (off-peak)
- **Deferred routing**: Analytics → analytics_queue (low priority)

---

## Task Flow Diagram

### Primary Flow: Transaction Created

```
Transaction Created
    │
    ├─> Store in Database
    │
    ├─> Generate Correlation ID (UUID)
    │
    ├─> Publish Event: "transaction.created"
    │   ├─ transaction_id: UUID
    │   ├─ correlation_id: UUID
    │   ├─ timestamp: datetime
    │   └─ event_type: "transaction.created"
    │
    └─> Return 200 OK (non-blocking)
        │
        ▼ (Async)
    Celery Worker picks up task
        │
        ├─> predict_transaction_task(transaction_id, correlation_id)
        │   │
        │   ├─> Load Transaction (async DB)
        │   │
        │   ├─> FeatureExtractor.extract_all()
        │   │   ├─ TransactionFeatures
        │   │   ├─ CustomerFeatures
        │   │   ├─ MerchantFeatures
        │   │   ├─ DeviceFeatures
        │   │   └─ VelocityFeatures
        │   │
        │   ├─> RuleEngine.evaluate()
        │   │   ├─ Load 24 rules
        │   │   ├─ Evaluate each rule
        │   │   └─ Return composite score
        │   │
        │   ├─> Load ML Model (from registry)
        │   │   └─ predict_proba()
        │   │
        │   ├─> Combine Scores
        │   │   └─ final = (ml * 0.6) + (rules * 0.4)
        │   │
        │   ├─> Store Prediction
        │   │   ├─ Prediction record
        │   │   └─ PredictionExplanation records
        │   │
        │   ├─> IF risk > 0.7:
        │   │   └─> generate_fraud_alert_task.delay(prediction_id)
        │   │
        │   └─> update_analytics_task.delay()
        │
        └─> Log completion (structured JSON)
```

---

## Observability Design

### Structured Logging Format

```json
{
  "timestamp": "2026-06-20T05:00:00.123Z",
  "level": "INFO",
  "correlation_id": "uuid-here",
  "task_id": "uuid-here",
  "task_name": "predict_transaction_task",
  "transaction_id": "uuid-here",
  "event_type": "task.started",
  "duration_ms": 0,
  "status": "success",
  "error": null,
  "metadata": {
    "ml_score": 0.0,
    "rule_score": 0.0,
    "final_score": 0.0,
    "rules_triggered": 0,
    "model_version": "v1.0.0"
  }
}
```

### Metrics to Track

- **Prediction latency**: P95, P99, mean
- **Throughput**: Predictions/second
- **Error rate**: Failed tasks/total tasks
- **Queue depth**: Tasks waiting per queue
- **Worker utilization**: Active workers/total workers
- **Retry rate**: Retried tasks/total tasks

---

## Retry + Failure Handling

### Retry Policy

```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True,  # Add randomness
)
def predict_transaction_task(self, transaction_id: UUID):
    try:
        # Task logic
        pass
    except DatabaseError as exc:
        raise self.retry(exc=exc, countdown=60)
    except ModelLoadError as exc:
        raise self.retry(exc=exc, countdown=300)
```

### Failure Handling

- **Dead Letter Queue**: Failed tasks stored in `failed_tasks` table
- **Idempotency**: Use transaction_id as idempotency key
- **Manual retry**: Admin can retry from dashboard
- **Alert on failure**: Notify ops team if failure rate > 5%

---

## Implementation Plan

### Phase 1: Core Infrastructure (Now)
1. ✅ Celery app initialization
2. ✅ Queue definitions
3. ✅ Task decorators and base configuration
4. ✅ prediction_tasks.py (core prediction)
5. ✅ Transaction event trigger integration

### Phase 2: Supporting Tasks (Next)
- alert_tasks.py
- model_tasks.py
- analytics_tasks.py

### Phase 3: Integration (Next)
- Modify TransactionService to publish events
- Add structured logging
- Add metrics tracking

---

## Configuration

### Environment Variables

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ACKS_LATE=true
CELERY_TASK_REJECT_ON_WORKER_LOSE=true
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Queues
QUEUE_FRAUD_PREDICTION=fraud_prediction_queue
QUEUE_ALERT_GENERATION=alert_generation_queue
QUEUE_MODEL_TRAINING=model_training_queue
QUEUE_ANALYTICS=analytics_queue
```

---

## Performance Requirements

- **Latency**: P95 < 500ms per prediction
- **Throughput**: 1000 predictions/second (with 8 workers)
- **Batch**: Support 10K+ predictions in single task
- **Scalability**: Horizontal scaling via worker addition
- **Availability**: 99.9% uptime (Redis persistence)

---

## Security

- Task authentication via Redis ACL
- Encrypted broker connection (rediss://)
- Input validation with Pydantic
- No sensitive data in task arguments

---

## Monitoring

- Flower dashboard for task monitoring
- Structured logs (JSON) → ELK/Loki
- Metrics → Prometheus/Grafana
- Alerts → PagerDuty/Opsgenie
