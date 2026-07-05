"""
Blacklist-based fraud detection rules.

Detects blacklisted merchants, devices, and other entities.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class BlacklistedMerchantRule(BaseRule):
    """
    Detects transactions from blacklisted merchants.

    Triggers when transaction involves a merchant on the blacklist.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_005"

    @property
    def rule_name(self) -> str:
        return "Blacklisted Merchant"

    @property
    def description(self) -> str:
        return "Transaction involves a blacklisted merchant"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate blacklisted merchant rule."""
        merchant_risk = features.get("merchant_risk_score", 0.0)
        merchant_fraud_count = features.get("merchant_fraud_count_90d", 0)

        if merchant_risk > 0.8:
            return self._create_result(
                triggered=True,
                score=0.9,
                explanation=f"Merchant has high risk score: {merchant_risk:.2f}",
                metadata={"merchant_risk_score": merchant_risk},
            )

        if merchant_fraud_count >= 3:
            return self._create_result(
                triggered=True,
                score=0.8,
                explanation=f"Merchant has {merchant_fraud_count} fraud cases in last 90 days",
                metadata={"merchant_fraud_count_90d": merchant_fraud_count},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Merchant not blacklisted",
        )


class BlacklistedDeviceRule(BaseRule):
    """
    Detects transactions from blacklisted devices.

    Triggers when transaction involves a device on the blacklist.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_006"

    @property
    def rule_name(self) -> str:
        return "Blacklisted Device"

    @property
    def description(self) -> str:
        return "Transaction involves a device associated with fraud"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate blacklisted device rule."""
        device_fraud_history = features.get("device_fraud_history", 0)
        device_risk = features.get("device_risk_score", 0.0)

        if device_fraud_history or device_risk > 0.7:
            return self._create_result(
                triggered=True,
                score=0.85,
                explanation=f"Device has fraud history or high risk score",
                metadata={"device_fraud_history": device_fraud_history, "device_risk": device_risk},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Device not blacklisted",
        )


class BlacklistedIPRule(BaseRule):
    """
    Detects transactions from blacklisted IP addresses.

    Triggers when transaction originates from a suspicious IP.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_007"

    @property
    def rule_name(self) -> str:
        return "Blacklisted IP Address"

    @property
    def description(self) -> str:
        return "Transaction originates from a suspicious IP address"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate blacklisted IP rule."""
        ip_risk = features.get("device_ip_risk", 0.0)

        if ip_risk > 0.8:
            return self._create_result(
                triggered=True,
                score=0.8,
                explanation=f"IP address has high reputation risk: {ip_risk:.2f}",
                metadata={"ip_risk": ip_risk},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="IP address not blacklisted",
        )
