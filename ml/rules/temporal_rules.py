"""
Temporal-based fraud detection rules.

Detects suspicious timing patterns like night transactions, unusual hours.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class NightTransactionRule(BaseRule):
    """
    Detects transactions during unusual hours.

    Triggers for transactions between 11 PM and 5 AM.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_008"

    @property
    def rule_name(self) -> str:
        return "Night Transaction"

    @property
    def description(self) -> str:
        return "Transaction occurred during unusual hours (11 PM - 5 AM)"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.LOW

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate night transaction rule."""
        hour_of_day = features.get("hour_of_day", 12)
        is_night = features.get("is_night", 0)

        if is_night or (hour_of_day >= 23 or hour_of_day < 5):
            return self._create_result(
                triggered=True,
                score=0.3,
                explanation=f"Transaction at unusual hour: {hour_of_day:02d}:00",
                metadata={"hour_of_day": hour_of_day},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Transaction during normal hours",
        )


class WeekendTransactionRule(BaseRule):
    """
    Detects unusual weekend transaction patterns.

    Triggers for high-value transactions on weekends.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_009"

    @property
    def rule_name(self) -> str:
        return "Weekend High-Value Transaction"

    @property
    def description(self) -> str:
        return "High-value transaction on weekend"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.LOW

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate weekend transaction rule."""
        is_weekend = features.get("is_weekend", 0)
        amount = features.get("amount", 0.0)
        avg_spending = features.get("avg_spending", 1.0)

        if is_weekend and amount > (avg_spending * 2):
            return self._create_result(
                triggered=True,
                score=0.3,
                explanation="High-value transaction on weekend",
                metadata={"amount": amount, "is_weekend": is_weekend},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Weekend transaction normal",
        )


class DormantAccountRule(BaseRule):
    """
    Detects transactions from dormant accounts.

    Triggers when account has been inactive for extended period.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_010"

    @property
    def rule_name(self) -> str:
        return "Dormant Account Activity"

    @property
    def description(self) -> str:
        return "Transaction from account inactive for extended period"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate dormant account rule."""
        days_since_last = features.get("days_since_last_tx", 0)
        account_age = features.get("customer_account_age_days", 0)

        if days_since_last > 90 and days_since_last < account_age:
            score = min(1.0, days_since_last / 365.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Account dormant for {days_since_last} days",
                metadata={"days_since_last_tx": days_since_last},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Account not dormant",
        )
