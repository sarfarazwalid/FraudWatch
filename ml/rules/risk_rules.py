"""
Customer and merchant risk rules.

Detects high-risk customers, fraud history, suspicious patterns.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class HighRiskCustomerRule(BaseRule):
    """
    Detects high-risk customers.

    Triggers when customer has high historical risk score.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_011"

    @property
    def rule_name(self) -> str:
        return "High-Risk Customer"

    @property
    def description(self) -> str:
        return "Customer has high historical risk score"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate high-risk customer rule."""
        risk_score = features.get("customer_risk_score", 0.0)
        fraud_history = features.get("customer_fraud_history", 0)

        if risk_score > 0.7:
            score = min(1.0, risk_score)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Customer has high risk score: {risk_score:.2f}",
                metadata={"customer_risk_score": risk_score},
            )

        if fraud_history:
            return self._create_result(
                triggered=True,
                score=0.8,
                explanation="Customer has history of fraud",
                metadata={"customer_fraud_history": fraud_history},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Customer risk normal",
        )


class NewCustomerRule(BaseRule):
    """
    Detects new customers (account age < 7 days).

    Triggers for very new accounts.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_012"

    @property
    def rule_name(self) -> str:
        return "New Customer Account"

    @property
    def description(self) -> str:
        return "Transaction from newly created account"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.LOW

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate new customer rule."""
        account_age = features.get("customer_account_age_days", 999)

        if account_age < 7:
            score = max(0.0, (7 - account_age) / 7.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Account created {account_age} days ago",
                metadata={"account_age_days": account_age},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Account not new",
        )


class UnusualSpendingRule(BaseRule):
    """
    Detects unusual spending patterns.

    Triggers when transaction deviates significantly from normal behavior.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_013"

    @property
    def rule_name(self) -> str:
        return "Unusual Spending Pattern"

    @property
    def description(self) -> str:
        return "Transaction deviates from customer's spending pattern"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate unusual spending rule."""
        amount = features.get("amount", 0.0)
        avg_spending = features.get("avg_spending", 1.0)
        std_spending = features.get("std_spending", 0.0)

        if avg_spending > 0 and std_spending > 0:
            z_score = (amount - avg_spending) / std_spending

            if z_score > 4:
                score = min(1.0, z_score / 10.0)
                return self._create_result(
                    triggered=True,
                    score=score,
                    explanation=f"Transaction is {z_score:.1f} std deviations from mean",
                    metadata={"z_score": z_score, "avg": avg_spending, "std": std_spending},
                )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Spending pattern normal",
        )
