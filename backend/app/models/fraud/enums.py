"""
Fraud Domain Enumerations.

Defines all enumerated types specific to fraud detection and investigation.
"""

from enum import Enum


class AlertSeverity(str, Enum):
    """Fraud alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Fraud alert lifecycle status."""
    NEW = "new"
    TRIAGED = "triaged"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    FALSE_POSITIVE = "false_positive"


class CasePriority(str, Enum):
    """Fraud case priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, Enum):
    """Fraud investigation case statuses."""
    NEW = "new"
    TRIAGED = "triaged"
    UNDER_INVESTIGATION = "under_investigation"
    ESCALATED = "escalated"
    AWAITING_CUSTOMER = "awaiting_customer"
    CONFIRMED_FRAUD = "confirmed_fraud"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DetectionMethod(str, Enum):
    """Fraud detection methods."""
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"
    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    NETWORK = "network"
    MANUAL = "manual"
    HYBRID = "hybrid"


class PredictionLabel(str, Enum):
    """ML model prediction labels."""
    FRAUD = "fraud"
    LEGITIMATE = "legitimate"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"


class RiskDecision(str, Enum):
    """Risk assessment decisions."""
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"
    BLOCK = "block"
    ESCALATE = "escalate"


class TimelineActionType(str, Enum):
    """Investigation timeline action types."""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_ADDED = "attachment_added"
    NOTE_ADDED = "note_added"
    CUSTOMER_CONTACTED = "customer_contacted"
    EVIDENCE_ADDED = "evidence_added"
    CLOSED = "closed"
    REOPENED = "reopened"


class CommentVisibility(str, Enum):
    """Comment visibility levels."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    RESTRICTED = "restricted"


class AttachmentType(str, Enum):
    """Fraud attachment file types."""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SPREADSHEET = "spreadsheet"
    LOG_FILE = "log_file"
    SCREENSHOT = "screenshot"
    OTHER = "other"


class ExplanationMethod(str, Enum):
    """Model explanation methods."""
    SHAP = "shap"
    LIME = "lime"
    FEATURE_IMPORTANCE = "feature_importance"
    RULE_EXPLANATION = "rule_explanation"
    COUNTERFACTUAL = "counterfactual"
    ATTENTION = "attention"
    OTHER = "other"