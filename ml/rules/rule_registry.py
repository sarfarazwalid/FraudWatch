"""
Rule registry for managing fraud detection rules.

Provides centralized registration, discovery, and management
of all fraud detection rules.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule


class RuleRegistry:
    """
    Central registry for all fraud detection rules.

    Provides:
    - Rule registration and discovery
    - Rule metadata management
    - Rule lookup by ID or category
    """

    def __init__(self):
        """Initialize empty rule registry."""
        self._rules: dict[str, BaseRule] = {}

    def register(self, rule: BaseRule) -> None:
        """
        Register a rule.

        Args:
            rule: Rule instance to register

        Raises:
            ValueError: If rule with same ID already registered
        """
        if rule.rule_id in self._rules:
            raise ValueError(f"Rule {rule.rule_id} already registered")

        self._rules[rule.rule_id] = rule

    def unregister(self, rule_id: str) -> None:
        """
        Unregister a rule.

        Args:
            rule_id: Rule identifier to remove
        """
        if rule_id in self._rules:
            del self._rules[rule_id]

    def get_rule(self, rule_id: str) -> BaseRule | None:
        """
        Get rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule instance or None
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[BaseRule]:
        """
        Get all registered rules.

        Returns:
            List of all rules
        """
        return list(self._rules.values())

    def get_enabled_rules(self) -> list[BaseRule]:
        """
        Get all enabled rules.

        Returns:
            List of enabled rules
        """
        return [rule for rule in self._rules.values() if rule.enabled]

    def get_rules_by_severity(self, severity: str) -> list[BaseRule]:
        """
        Get rules by severity level.

        Args:
            severity: Severity level (low, medium, high, critical)

        Returns:
            List of matching rules
        """
        return [
            rule for rule in self._rules.values()
            if rule.severity.value == severity
        ]

    def enable_rule(self, rule_id: str) -> None:
        """
        Enable a rule.

        Args:
            rule_id: Rule identifier
        """
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True

    def disable_rule(self, rule_id: str) -> None:
        """
        Disable a rule.

        Args:
            rule_id: Rule identifier
        """
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self._rules)
        enabled = sum(1 for rule in self._rules.values() if rule.enabled)

        by_severity = {}
        for rule in self._rules.values():
            severity = rule.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_rules": total,
            "enabled_rules": enabled,
            "disabled_rules": total - enabled,
            "by_severity": by_severity,
        }

    def clear(self) -> None:
        """Clear all registered rules."""
        self._rules.clear()
