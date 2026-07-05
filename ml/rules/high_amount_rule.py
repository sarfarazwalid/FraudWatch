"""
High transaction amount rule.

Detects transactions with unusually high amounts.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class HighAmountRule(BaseRule):
    """
    Detects high-value transactions.

    Triggers when transaction amount exceeds threshold
    relative to customer's historical average.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_001"

    @property
    def rule_name(self) -> str:
        return "High Transaction Amount"

    @property
    def description(self) -> str:
        return "Transaction amount is significantly higher than customer's average"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """
        Evaluate high amount rule.

        Args:
            transaction_data: Raw transaction data
            features: Extracted features

        Returns:
            RuleResult
        """
        amount = features.get("amount", 0.0)
        avg_spending = features.get("avg_spending", 1.0)
        z_score = features.get("amount_zscore", 0.0)

        # Threshold: 3x average OR z-score > 5
        threshold_multiplier = 3.0
        z_score_threshold = 5.0

        if avg_spending > 0 and amount > (avg_spending * threshold_multiplier):
            ratio = amount / avg_spending
            score = min(1.0, ratio / 10.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Transaction amount ({amount:.2f}) is {ratio:.1f}x customer average ({avg_spending:.2f})",
                metadata={"amount": amount, "avg_spending": avg_spending, "ratio": ratio},
            )

        if z_score > z_score_threshold:
            score = min(1.0, z_score / 10.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Amount z-score ({z_score:.2f}) exceeds threshold ({z_score_threshold})",
                metadata={"z_score": z_score},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Transaction amount within normal range",
        )
