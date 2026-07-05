"""
Velocity-based fraud detection rules.

Detects rapid transactions, high frequency, and unusual velocity patterns.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class RapidTransactionRule(BaseRule):
    """
    Detects rapid successive transactions.

    Triggers when multiple transactions occur within short time windows.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_002"

    @property
    def rule_name(self) -> str:
        return "Rapid Transactions"

    @property
    def description(self) -> str:
        return "Multiple transactions occurring within short time windows"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate rapid transaction rule."""
        tx_count_1h = features.get("tx_count_1h", 0)
        tx_count_24h = features.get("tx_count_24h", 0)
        rapid_detected = features.get("rapid_tx_detected", 0)

        if rapid_detected or tx_count_1h >= 5:
            score = min(1.0, tx_count_1h / 20.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Rapid transactions detected: {tx_count_1h} in last hour",
                metadata={"tx_count_1h": tx_count_1h},
            )

        if tx_count_24h > 20:
            score = min(1.0, tx_count_24h / 100.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"High transaction frequency: {tx_count_24h} in last 24 hours",
                metadata={"tx_count_24h": tx_count_24h},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Transaction velocity within normal range",
        )


class ImpossibleTravelRule(BaseRule):
    """
    Detects impossible travel scenarios.

    Triggers when transactions occur from geographically distant locations
    within an implausible time window.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_003"

    @property
    def rule_name(self) -> str:
        return "Impossible Travel"

    @property
    def description(self) -> str:
        return "Transaction from location that's geographically impossible to reach"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate impossible travel rule."""
        distance_km = features.get("geographic_distance_km", 0.0)
        hours_since_last = features.get("hours_since_last_tx", 999)

        # Impossible if >500km in <2 hours
        if distance_km > 500 and hours_since_last < 2:
            speed_needed = distance_km / max(hours_since_last, 0.1)
            score = min(1.0, speed_needed / 1000.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Impossible travel: {distance_km:.0f}km in {hours_since_last:.1f}h (needed {speed_needed:.0f} km/h)",
                metadata={"distance_km": distance_km, "hours": hours_since_last},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Travel pattern normal",
        )


class HighVelocityRule(BaseRule):
    """
    Detects high transaction velocity.

    Triggers when transaction velocity exceeds normal patterns.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_004"

    @property
    def rule_name(self) -> str:
        return "High Velocity"

    @property
    def description(self) -> str:
        return "Transaction velocity exceeds normal patterns"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate high velocity rule."""
        velocity_score = features.get("velocity_score", 0.0)

        if velocity_score > 0.7:
            return self._create_result(
                triggered=True,
                score=velocity_score,
                explanation=f"High velocity score: {velocity_score:.2f}",
                metadata={"velocity_score": velocity_score},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Velocity normal",
        )
