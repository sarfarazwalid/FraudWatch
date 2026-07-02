#!/usr/bin/env python3
"""
Verification script for Fraud Domain ORM models.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    # Test imports
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
    from app.models.fraud.enums import (
        AlertSeverity,
        AlertStatus,
        CasePriority,
        CaseStatus,
        DetectionMethod,
        PredictionLabel,
        RiskDecision,
        TimelineActionType,
        CommentVisibility,
        AttachmentType,
        ExplanationMethod,
    )
    
    print("✓ All fraud models imported successfully")
    
    # Verify model inheritance
    from app.models.base import Base
    from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin, VersionMixin
    
    fraud_models = [
        FraudAlert, FraudCase, FraudRule, Prediction, PredictionExplanation,
        RiskAssessment, InvestigationTimeline, FraudComment, FraudAttachment
    ]
    
    for model in fraud_models:
        assert issubclass(model, Base), f"{model.__name__} doesn't inherit from Base"
        assert hasattr(model, '__tablename__'), f"{model.__name__} missing __tablename__"
        print(f"✓ {model.__name__:25s} - valid model")
    
    # Verify enums
    enums = [
        AlertSeverity, AlertStatus, CasePriority, CaseStatus, DetectionMethod,
        PredictionLabel, RiskDecision, TimelineActionType, CommentVisibility,
        AttachmentType, ExplanationMethod
    ]
    
    for enum in enums:
        assert issubclass(enum, str), f"{enum.__name__} should inherit from str"
        print(f"✓ {enum.__name__:30s} - valid enum")
    
    print("\n✅ All validation checks passed!")
    
except Exception as e:
    print(f"❌ Validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)