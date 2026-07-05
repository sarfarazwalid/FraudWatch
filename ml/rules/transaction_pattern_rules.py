"""
Transaction pattern fraud detection rules.

Detects suspicious transaction patterns like card testing, synthetic identity.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class CardTestingRule(BaseRule):
    """
    Detects card testing patterns.

    Triggers when multiple small transactions occur (card testing).
    """

    @property
    def rule_id(self) -> str:
        return "RULE_020"

    @property
    def rule_name(self) -> str:
        return "Card Testing Pattern"

    @property
    def description(self) -> str:
        return "Multiple small transactions suggest card testing"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate card testing rule."""
        amount = features.get("amount", 0.0)
        tx_count_1h = features.get("tx_count_1h", 0)
        avg_spending = features.get("avg_spending", 1.0)

        # Card testing: many small transactions
        if tx_count_1h >= 3 and amount < (avg_spending * 0.2):
            return self._create_result(
                triggered=True,
                score=0.8,
                explanation=f"Potential card testing: {tx_count_1h} small transactions in 1 hour",
                metadata={"tx_count_1h": tx_count_1h, "amount": amount},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="No card testing pattern",
        )


class SyntheticIdentityRule(BaseRule):
    """
    Detects synthetic identity indicators.

    Triggers when multiple risk factors suggest synthetic identity.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_021"

    @property
    def rule_name(self) -> str:
        return "Synthetic Identity Indicators"

    @property
    def description(self) -> str:
        return "Multiple indicators suggest synthetic identity"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate synthetic identity rule."""
        is_new_device = features.get("is_new_device", 0)
        account_age = features.get("customer_account_age_days", 999)
        is_new_merchant = features.get("is_new_merchant", 0)

        risk_indicators = 0

        if is_new_device:
            risk_indicators += 1
        if account_age < 7:
            risk_indicators += 1
        if is_new_merchant:
            risk_indicators += 1

        if risk_indicators >= 2:
            score = min(1.0, risk_indicators / 4.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"Multiple synthetic identity indicators: {risk_indicators}",
                metadata={"risk_indicators": risk_indicators},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="No synthetic identity pattern",
        )


class UnusualTransactionTypeRule(BaseRule):
    """
    Detects unusual transaction type for customer.

    Triggers when transaction type differs from customer's normal pattern.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_022"

    @property
    def rule_name(self) -> str:
        return "Unusual Transaction Type"

    @property
    def description(self) -> str:
        return "Transaction type unusual for this customer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.LOW

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate unusual transaction type rule."""
        tx_type_encoded = features.get("transaction_type_encoded", 0)

        # Placeholder logic - in production compare to customer history
        if tx_type_encoded > 5:  # High encoded value = unusual type
            return self._create_result(
                triggered=True,
                score=0.3,
                explanation="Unusual transaction type for customer",
                metadata={"transaction_type_encoded": tx_type_encoded},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Transaction type normal",
        )


class CurrencyMismatchRule(BaseRule):
    """
    Detects currency mismatches.

    Triggers when transaction currency doesn't match customer's usual currency.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_023"

    @property
    def rule_name(self) -> str:
        return "Currency Mismatch"

    @property
    def description(self) -> str:
        return "Transaction currency doesn't match customer's usual currency"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate currency mismatch rule."""
        currency_encoded = features.get("currency_encoded", 0)

        if currency_encoded > 0:  # Non-zero indicates unusual currency
            return self._create_result(
                triggered=True,
                score=0.5,
                explanation="Transaction in unusual currency",
                metadata={"currency_encoded": currency_encoded},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Currency normal",
        )


class CountryMismatchRule(BaseRule):
    """
    Detects country mismatches.

    Triggers when transaction country doesn't match customer's usual country.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_024"

    @property
    def rule_name(self) -> str:
        return "Country Mismatch"

    @property
    def description(self) -> str:
        return "Transaction country doesn't match customer's usual country"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate country mismatch rule."""
        country_encoded = features.get("country_encoded", 0)

        if country_encoded > 0:  # Non-zero indicates unusual country
            return self._create_result(
                triggered=True,
                score=0.5,
                explanation="Transaction from unusual country",
                metadata={"country_encoded": country_encoded},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Country normal",
        )
