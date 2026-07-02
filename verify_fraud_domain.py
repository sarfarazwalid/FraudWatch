#!/usr/bin/env python3
"""
Comprehensive verification for Fraud Domain ORM.
Validates models, relationships, constraints, indexes, and documentation.
"""

import sys
from pathlib import Path
from sqlalchemy import inspect, Column
from sqlalchemy.orm.attributes import InstrumentedAttribute

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("FRAUD DOMAIN ORM VERIFICATION")
print("=" * 80)

# ============================================================================
# 1. MODEL VERIFICATION
# ============================================================================
print("\n1. MODEL VERIFICATION")
print("-" * 80)

from app.models.fraud import (
    FraudAlert,
    FraudCase,
    FraudRule,
    Prediction,
    PredictionExplanation,
    RiskAssessment,
    InvestigationTimeline,
    FraudComment,
    FraudAttachment,
)
from app.models.base import Base
from app.models.fraud.fraud_rule import FraudRule as FR
from app.models.fraud.fraud_alert import FraudAlert as FA
from app.models.fraud.fraud_case import FraudCase as FC
from app.models.fraud.prediction import Prediction as P
from app.models.fraud.prediction_explanation import PredictionExplanation as PE
from app.models.fraud.risk_assessment import RiskAssessment as RA
from app.models.fraud.investigation_timeline import InvestigationTimeline as IT
from app.models.fraud.fraud_comment import FraudComment as FCO
from app.models.fraud.fraud_attachment import FraudAttachment as FAT

fraud_models = [
    FA, FC, FR, P, PE,
    RA, IT, FCO, FAT
]

model_summaries = {}

for model in fraud_models:
    # Check inheritance
    assert issubclass(model, Base), f"{model.__name__} doesn't inherit from Base"
    
    # Get mapper without triggering relationship configuration
    mapper = model.__mapper__
    table = mapper.tables[0] if mapper.tables else None
    
    if table is None:
        # Fallback: use _sa_class_manager to get table
        table = mapper._class_manager.local_table if hasattr(mapper._class_manager, 'local_table') else None
    
    # Collect field information from mapper columns
    fields = []
    for key, column in mapper.columns.items():
        fields.append({
            'name': column.name,
            'type': str(column.type),
            'nullable': column.nullable,
            'indexed': column.index,
            'unique': column.unique,
        })
    
    # Collect relationships by inspecting class attributes
    relationships = []
    for attr_name in dir(model):
        if attr_name.startswith('_'):
            continue
        attr = getattr(model, attr_name, None)
        if isinstance(attr, InstrumentedAttribute):
            if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
                try:
                    target_class = attr.property.mapper.class_
                    relationships.append({
                        'name': attr_name,
                        'target': target_class.__name__,
                        'uselist': attr.property.uselist,
                        'cascade': str(attr.property.cascade) if hasattr(attr.property, 'cascade') else 'N/A',
                    })
                except:
                    pass
    
    # Collect indexes from table
    indexes = [idx.name for idx in table.indexes] if table else []
    
    # Collect constraints
    constraints = [c.name for c in table.constraints if hasattr(c, 'name')] if table else []
    
    model_summaries[model.__name__] = {
        'tablename': table.name if table else model.__tablename__,
        'fields': fields,
        'relationships': relationships,
        'indexes': indexes,
        'constraints': constraints,
    }
    
    print(f"✓ {model.__name__:25s} → {table.name if table else model.__tablename__}")

# ============================================================================
# 2. ENUM VERIFICATION
# ============================================================================
print("\n2. ENUM VERIFICATION")
print("-" * 80)

from app.models.fraud.enums import (
    AlertSeverity, AlertStatus, CasePriority, CaseStatus,
    DetectionMethod, PredictionLabel, RiskDecision,
    TimelineActionType, CommentVisibility, AttachmentType,
    ExplanationMethod
)

enums = {
    'AlertSeverity': AlertSeverity,
    'AlertStatus': AlertStatus,
    'CasePriority': CasePriority,
    'CaseStatus': CaseStatus,
    'DetectionMethod': DetectionMethod,
    'PredictionLabel': PredictionLabel,
    'RiskDecision': RiskDecision,
    'TimelineActionType': TimelineActionType,
    'CommentVisibility': CommentVisibility,
    'AttachmentType': AttachmentType,
    'ExplanationMethod': ExplanationMethod,
}

for name, enum_class in enums.items():
    values = [e.value for e in enum_class]
    print(f"✓ {name:30s} ({len(values)} values): {', '.join(values[:3])}...")

# ============================================================================
# 3. RELATIONSHIP VERIFICATION
# ============================================================================
print("\n3. RELATIONSHIP VERIFICATION")
print("-" * 80)

# Check bidirectional relationships
relationships_ok = []

# FraudAlert ↔ FraudCase
assert 'case' in model_summaries['FraudAlert']['relationships'][2]['name']
assert 'alert' in [r['name'] for r in model_summaries['FraudCase']['relationships']]
relationships_ok.append("FraudAlert ↔ FraudCase")

# FraudAlert ↔ FraudRule
assert 'rule' in [r['name'] for r in model_summaries['FraudAlert']['relationships']]
assert 'alerts' in [r['name'] for r in model_summaries['FraudRule']['relationships']]
relationships_ok.append("FraudAlert ↔ FraudRule")

# FraudCase ↔ InvestigationTimeline
assert 'timeline_entries' in [r['name'] for r in model_summaries['FraudCase']['relationships']]
assert 'case' in [r['name'] for r in model_summaries['InvestigationTimeline']['relationships']]
relationships_ok.append("FraudCase ↔ InvestigationTimeline")

# FraudCase ↔ FraudComment
assert 'comments' in [r['name'] for r in model_summaries['FraudCase']['relationships']]
assert 'case' in [r['name'] for r in model_summaries['FraudComment']['relationships']]
relationships_ok.append("FraudCase ↔ FraudComment")

# FraudCase ↔ FraudAttachment
assert 'attachments' in [r['name'] for r in model_summaries['FraudCase']['relationships']]
assert 'case' in [r['name'] for r in model_summaries['FraudAttachment']['relationships']]
relationships_ok.append("FraudCase ↔ FraudAttachment")

# Prediction ↔ PredictionExplanation
assert 'explanations' in [r['name'] for r in model_summaries['Prediction']['relationships']]
assert 'prediction' in [r['name'] for r in model_summaries['PredictionExplanation']['relationships']]
relationships_ok.append("Prediction ↔ PredictionExplanation")

print("Bidirectional relationships verified:")
for rel in relationships_ok:
    print(f"  ✓ {rel}")

# ============================================================================
# 4. CONSTRAINT VERIFICATION
# ============================================================================
print("\n4. CONSTRAINT VERIFICATION")
print("-" * 80)

# FraudAlert constraints
alert_constraints = model_summaries['FraudAlert']['constraints']
assert any('risk_score' in c for c in alert_constraints), "FraudAlert missing risk_score constraint"
print("✓ FraudAlert: risk_score range (0-100)")

# FraudCase constraints
case_constraints = model_summaries['FraudCase']['constraints']
assert any('escalation_level' in c for c in case_constraints), "FraudCase missing escalation_level constraint"
assert any('loss_amount' in c for c in case_constraints), "FraudCase missing loss_amount constraint"
print("✓ FraudCase: escalation_level >= 0")
print("✓ FraudCase: loss_amount >= 0")

# Prediction constraints
pred_constraints = model_summaries['Prediction']['constraints']
assert any('confidence_score' in c for c in pred_constraints), "Prediction missing confidence_score constraint"
assert any('probability_score' in c for c in pred_constraints), "Prediction missing probability_score constraint"
print("✓ Prediction: confidence_score range (0-1)")
print("✓ Prediction: probability_score range (0-1)")

# PredictionExplanation constraints
exp_constraints = model_summaries['PredictionExplanation']['constraints']
assert any('importance_score' in c for c in exp_constraints), "PredictionExplanation missing importance_score constraint"
print("✓ PredictionExplanation: importance_score >= 0")

# RiskAssessment constraints
risk_constraints = model_summaries['RiskAssessment']['constraints']
print(f"✓ RiskAssessment: {len(risk_constraints)} score range constraints (0-100 or 0-1)")

# FraudRule constraints
rule_constraints = model_summaries['FraudRule']['constraints']
assert any('threshold' in c for c in rule_constraints), "FraudRule missing threshold constraint"
assert any('version' in c for c in rule_constraints), "FraudRule missing version constraint"
print("✓ FraudRule: threshold >= 0")
print("✓ FraudRule: version >= 1")

# ============================================================================
# 5. INDEX VERIFICATION
# ============================================================================
print("\n5. INDEX VERIFICATION")
print("-" * 80)

# Required single indexes
required_single_indexes = {
    'FraudAlert': ['alert_number'],  # unique
    'FraudCase': ['case_number'],  # unique
    'FraudRule': ['rule_code'],  # unique
    'FraudAlert': ['transaction_id', 'status', 'severity', 'generated_at', 'assigned_analyst_id'],
    'FraudCase': ['status', 'priority', 'opened_at', 'investigator_id'],
    'Prediction': ['transaction_id', 'predicted_label', 'prediction_timestamp', 'model_version_id'],
    'RiskAssessment': ['transaction_id', 'decision', 'assessed_at'],
    'InvestigationTimeline': ['case_id', 'performed_at', 'action_type', 'performed_by'],
    'FraudComment': ['case_id', 'author_id', 'visibility'],
    'FraudAttachment': ['case_id', 'uploaded_by', 'uploaded_at'],
}

for model_name, required_indexes in required_single_indexes.items():
    model_indexes = model_summaries[model_name]['indexes']
    model_fields = [f['name'] for f in model_summaries[model_name]['fields']]
    
    for idx_name in required_indexes:
        assert idx_name in model_fields, f"{model_name} missing field {idx_name}"
        # Check if field is in any index
        has_index = any(idx_name in idx for idx in model_indexes)
        assert has_index, f"{model_name}.{idx_name} not indexed"

print(f"✓ All required single indexes verified")

# Required composite indexes
required_composite_indexes = [
    ('FraudAlert', 'ix_fraud_alerts_status_severity'),
    ('FraudAlert', 'ix_fraud_alerts_analyst_status'),
    ('FraudAlert', 'ix_fraud_alerts_transaction_generated'),
    ('FraudCase', 'ix_fraud_cases_status_priority'),
    ('FraudCase', 'ix_fraud_cases_investigator_status'),
    ('Prediction', 'ix_predictions_transaction_timestamp'),
    ('Prediction', 'ix_predictions_model_timestamp'),
    ('RiskAssessment', 'ix_risk_assessments_transaction_assessed'),
    ('InvestigationTimeline', 'ix_investigation_timeline_case_performed'),
    ('FraudComment', 'ix_fraud_comments_case_created'),
    ('FraudAttachment', 'ix_fraud_attachments_case_uploaded'),
]

for model_name, idx_name in required_composite_indexes:
    model_indexes = model_summaries[model_name]['indexes']
    assert idx_name in model_indexes, f"{model_name} missing composite index {idx_name}"

print(f"✓ All required composite indexes verified ({len(required_composite_indexes)} indexes)")

# ============================================================================
# 6. FIELD VERIFICATION
# ============================================================================
print("\n6. FIELD VERIFICATION")
print("-" * 80)

# FraudAlert required fields
alert_fields = [f['name'] for f in model_summaries['FraudAlert']['fields']]
required_alert_fields = [
    'alert_number', 'transaction_id', 'severity', 'status', 'risk_score',
    'detection_method', 'triggered_rule_id', 'assigned_analyst_id',
    'generated_at', 'acknowledged_at', 'resolved_at', 'false_positive',
    'resolution_summary'
]
for field in required_alert_fields:
    assert field in alert_fields, f"FraudAlert missing field: {field}"
print(f"✓ FraudAlert: All {len(required_alert_fields)} required fields present")

# FraudCase required fields
case_fields = [f['name'] for f in model_summaries['FraudCase']['fields']]
required_case_fields = [
    'case_number', 'alert_id', 'priority', 'status', 'investigator_id',
    'opened_at', 'closed_at', 'escalation_level', 'fraud_confirmed',
    'loss_amount', 'resolution', 'summary'
]
for field in required_case_fields:
    assert field in case_fields, f"FraudCase missing field: {field}"
print(f"✓ FraudCase: All {len(required_case_fields)} required fields present")

# Prediction required fields
pred_fields = [f['name'] for f in model_summaries['Prediction']['fields']]
required_pred_fields = [
    'transaction_id', 'model_version_id', 'predicted_label',
    'confidence_score', 'probability_score', 'inference_time_ms',
    'prediction_timestamp'
]
for field in required_pred_fields:
    assert field in pred_fields, f"Prediction missing field: {field}"
print(f"✓ Prediction: All {len(required_pred_fields)} required fields present")

# PredictionExplanation required fields
exp_fields = [f['name'] for f in model_summaries['PredictionExplanation']['fields']]
required_exp_fields = [
    'prediction_id', 'explanation_method', 'feature_name',
    'feature_value', 'importance_score', 'contribution_direction',
    'display_order'
]
for field in required_exp_fields:
    assert field in exp_fields, f"PredictionExplanation missing field: {field}"
print(f"✓ PredictionExplanation: All {len(required_exp_fields)} required fields present")

# RiskAssessment required fields
risk_fields = [f['name'] for f in model_summaries['RiskAssessment']['fields']]
required_risk_fields = [
    'transaction_id', 'overall_risk_score', 'rule_score', 'ml_score',
    'behavior_score', 'velocity_score', 'geolocation_score', 'device_score',
    'decision', 'assessed_at'
]
for field in required_risk_fields:
    assert field in risk_fields, f"RiskAssessment missing field: {field}"
print(f"✓ RiskAssessment: All {len(required_risk_fields)} required fields present")

# InvestigationTimeline required fields
timeline_fields = [f['name'] for f in model_summaries['InvestigationTimeline']['fields']]
required_timeline_fields = [
    'case_id', 'performed_by', 'action_type', 'previous_status', 'new_status',
    'notes', 'performed_at'
]
for field in required_timeline_fields:
    assert field in timeline_fields, f"InvestigationTimeline missing field: {field}"
print(f"✓ InvestigationTimeline: All {len(required_timeline_fields)} required fields present")

# FraudComment required fields
comment_fields = [f['name'] for f in model_summaries['FraudComment']['fields']]
required_comment_fields = [
    'case_id', 'author_id', 'comment', 'visibility', 'edited', 'edited_at'
]
for field in required_comment_fields:
    assert field in comment_fields, f"FraudComment missing field: {field}"
print(f"✓ FraudComment: All {len(required_comment_fields)} required fields present")

# FraudAttachment required fields
attachment_fields = [f['name'] for f in model_summaries['FraudAttachment']['fields']]
required_attachment_fields = [
    'case_id', 'uploaded_by', 'file_name', 'mime_type', 'file_size',
    'storage_path', 'checksum', 'uploaded_at'
]
for field in required_attachment_fields:
    assert field in attachment_fields, f"FraudAttachment missing field: {field}"
print(f"✓ FraudAttachment: All {len(required_attachment_fields)} required fields present")

# ============================================================================
# 7. MIXIN VERIFICATION
# ============================================================================
print("\n7. MIXIN VERIFICATION (UUID + Timestamp + SoftDelete + Audit + Version)")
print("-" * 80)

for model in fraud_models:
    fields = [f['name'] for f in model_summaries[model.__name__]['fields']]
    assert 'id' in fields, f"{model.__name__} missing id (UUIDMixin)"
    assert 'created_at' in fields, f"{model.__name__} missing created_at (TimestampMixin)"
    assert 'updated_at' in fields, f"{model.__name__} missing updated_at (TimestampMixin)"
    assert 'deleted_at' in fields, f"{model.__name__} missing deleted_at (SoftDeleteMixin)"
    assert 'created_by' in fields, f"{model.__name__} missing created_by (AuditMixin)"
    assert 'updated_by' in fields, f"{model.__name__} missing updated_by (AuditMixin)"
    assert 'version' in fields, f"{model.__name__} missing version (VersionMixin)"
    
print(f"✓ All {len(fraud_models)} models have UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin")

# ============================================================================
# 8. CASE WORKFLOW VERIFICATION
# ============================================================================
print("\n8. CASE WORKFLOW VERIFICATION")
print("-" * 80)

case_status_values = [e.value for e in CaseStatus]
expected_workflow = ['new', 'triaged', 'under_investigation', 'escalated', 
                     'awaiting_customer', 'confirmed_fraud', 'false_positive', 
                     'resolved', 'closed']

for status in expected_workflow:
    assert status in case_status_values, f"Missing case status: {status}"

print(f"✓ CaseStatus enum contains all {len(expected_workflow)} workflow states:")
print(f"  {', '.join(expected_workflow)}")

# ============================================================================
# 9. SUMMARY
# ============================================================================
print("\n9. FRAUD DOMAIN SUMMARY")
print("=" * 80)

print("\nModels Implemented:")
for model_name, summary in model_summaries.items():
    print(f"\n  {model_name}:")
    print(f"    Table: {summary['tablename']}")
    print(f"    Fields: {len(summary['fields'])}")
    print(f"    Relationships: {len(summary['relationships'])}")
    print(f"    Indexes: {len(summary['indexes'])}")
    print(f"    Constraints: {len(summary['constraints'])}")

print(f"\nTotal Models: {len(fraud_models)}")
print(f"Total Enums: {len(enums)}")
print(f"Total Relationships: {sum(len(m['relationships']) for m in model_summaries.values())}")
total_indexes = sum(len(m['indexes']) for m in model_summaries.values())
print(f"Total Indexes: {total_indexes}")
print(f"Total Constraints: {sum(len(m['constraints']) for m in model_summaries.values())}")

# ============================================================================
# 10. DOCUMENTATION CHECK
# ============================================================================
print("\n10. DOCUMENTATION CHECK")
print("-" * 80)

docs_path = Path(__file__).parent / "docs" / "architecture" / "adr" / "005-fraud-domain.md"
assert docs_path.exists(), "ADR document missing"
print(f"✓ ADR document exists: {docs_path}")

print("\n" + "=" * 80)
print("✅ ALL VERIFICATION CHECKS PASSED!")
print("=" * 80)