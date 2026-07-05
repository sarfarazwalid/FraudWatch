"""
Merchant-based fraud detection rules.

Detects suspicious merchant patterns and merchant-related risks.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class HighRiskMerchantRule(BaseRule):
    """
    Detects high-risk merchant transactions.

    Triggers when merchant has high risk score or fraud history.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_017"

    @property
    def rule_name(self) -> str:
        return "High-Risk Merchant"

    @property
    def description(self) -> str:
        return "Transaction involves high-risk merchant"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate high-risk merchant rule."""
        merchant_risk = features.get("merchant_risk_score", 0.0)
        category_risk = features.get("merchant_category_risk", 0.0)

        if merchant_risk > 0.7:
            score = min(1.0, merchant_risk)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Merchant has high risk score: {merchant_risk:.2f}",
                metadata={"merchant_risk_score": merchant_risk},
            )

        if category_risk > 0.8:
            return self._create_result(
                triggered=True,
                score=0.7,
                explanation="Merchant category has high risk",
                metadata={"merchant_category_risk": category_risk},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Merchant risk normal",
        )


class UnverifiedMerchantRule(BaseRule):
    """
    Detects transactions with unverified merchants.

    Triggers for unverified merchants with high amounts.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_018"

    @property
    def rule_name(self) -> str:
        return "Unverified Merchant"

    @property
    def description(self) -> str:
        return "Transaction with unverified merchant"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate unverified merchant rule."""
        is_verified = features.get("merchant_is_verified", 0)
        amount = features.get("amount", 0.0)

        if not is_verified and amount > 1000:
            return self._create_result(
                triggered=True,
                score=0.6,
                explanation=f"High-value transaction with unverified merchant",
                metadata={"amount": amount},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Merchant verified or low amount",
        )


class RoundAmountRule(BaseRule):
    """
    Detects round amount transactions.

    Triggers for suspiciously round amounts (potential testing).
    """

    @property
    def rule_id(self) -> str:
        return "RULE_019"

    @property
    def rule_name(self) -> str:
        return "Round Amount Transaction"

    @property
    def description(self) -> str:
        return "Transaction with suspiciously round amount"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.LOW

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate round amount rule."""
        amount = features.get("amount", 0.0)

        # Check if amount is a round number (multiple of 100, 500, 1000)
        if amount >= 100 and amount % 100 == 0:
            return self._create_result(
                triggered=True,
                score=0.2,
                explanation=f"Round amount transaction: {amount:.0f}",
                metadata={"amount": amount},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Amount not suspiciously round",
        )
