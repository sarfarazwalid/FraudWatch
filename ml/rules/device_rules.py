"""
Device and channel fraud detection rules.

Detects new devices, device anomalies, and channel risks.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class NewDeviceRule(BaseRule):
    """
    Detects transactions from new devices.

    Triggers when device was first seen recently.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_014"

    @property
    def rule_name(self) -> str:
        return "New Device"

    @property
    def description(self) -> str:
        return "Transaction from a newly seen device"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate new device rule."""
        is_new_device = features.get("is_new_device", 0)
        device_age = features.get("device_age_days", 999)

        if is_new_device or device_age < 1:
            return self._create_result(
                triggered=True,
                score=0.5,
                explanation="Transaction from new device (first seen <24h ago)",
                metadata={"device_age_days": device_age},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Device not new",
        )


class DeviceCountryMismatchRule(BaseRule):
    """
    Detects device country mismatches.

    Triggers when device country differs from customer's usual country.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_015"

    @property
    def rule_name(self) -> str:
        return "Device Country Mismatch"

    @property
    def description(self) -> str:
        return "Device country doesn't match customer's usual country"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MEDIUM

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate device country mismatch rule."""
        device_country = features.get("device_country", 0)

        if device_country > 0:  # Non-zero indicates unusual country
            return self._create_result(
                triggered=True,
                score=0.5,
                explanation="Transaction from unusual device country",
                metadata={"device_country": device_country},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="Device country normal",
        )


class MultipleFailedAttemptsRule(BaseRule):
    """
    Detects multiple failed transaction attempts.

    Triggers when recent failed attempts are high.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_016"

    @property
    def rule_name(self) -> str:
        return "Multiple Failed Attempts"

    @property
    def description(self) -> str:
        return "Multiple failed transaction attempts detected"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    def evaluate(self, transaction_data: dict[str, Any], features: dict[str, Any]) -> RuleResult:
        """Evaluate multiple failed attempts rule."""
        failed_attempts = features.get("failed_attempts_24h", 0)

        if failed_attempts >= 5:
            score = min(1.0, failed_attempts / 20.0)
            return self._create_result(
                triggered=True,
                score=score,
                explanation=f"{failed_attempts} failed attempts in last 24 hours",
                metadata={"failed_attempts_24h": failed_attempts},
            )

        return self._create_result(
            triggered=False,
            score=0.0,
            explanation="No abnormal failed attempts",
        )
