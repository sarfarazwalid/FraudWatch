"""
Base rule interface and result structures.

Defines the contract that all fraud detection rules must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel


class RuleSeverity(str, Enum):
    """Rule severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    """
    Result of a single rule evaluation.

    Attributes:
        rule_id: Unique rule identifier
        rule_name: Human-readable rule name
        triggered: Whether rule was triggered
        score: Risk score contribution (0-1)
        severity: Rule severity level
        explanation: Human-readable explanation
        metadata: Additional rule-specific data
    """

    rule_id: str
    rule_name: str
    triggered: bool
    score: float
    severity: RuleSeverity
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseRule(ABC):
    """
    Abstract base class for all fraud detection rules.

    Each rule implements this interface to provide:
    - Rule metadata (ID, name, description)
    - Evaluation logic
    - Scoring mechanism
    - Explanation generation
    """

    def __init__(self):
        """Initialize rule with default configuration."""
        self._enabled = True
        self._weight = 1.0

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique rule identifier."""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable rule name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Rule description."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Rule version."""
        pass

    @property
    @abstractmethod
    def severity(self) -> RuleSeverity:
        """Rule severity level."""
        pass

    @property
    def weight(self) -> float:
        """Rule weight (default 1.0)."""
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        """Set rule weight."""
        self._weight = max(0.0, min(value, 10.0))

    @property
    def enabled(self) -> bool:
        """Whether rule is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable rule."""
        self._enabled = value

    @abstractmethod
    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """
        Evaluate rule against transaction.

        Args:
            transaction_data: Raw transaction data
            features: Extracted feature vector

        Returns:
            RuleResult with evaluation outcome
        """
        pass

    def _create_result(
        self,
        triggered: bool,
        score: float,
        explanation: str,
        metadata: dict[str, Any] | None = None,
    ) -> RuleResult:
        """
        Helper to create rule result.

        Args:
            triggered: Whether rule triggered
            score: Risk score contribution
            explanation: Human-readable explanation
            metadata: Optional metadata

        Returns:
            RuleResult instance
        """
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            triggered=triggered,
            score=score,
            severity=self.severity,
            explanation=explanation,
            metadata=metadata or {},
        )
