"""
Fraud detection rule engine orchestrator.

Executes multiple rules and aggregates results into a composite risk score.
"""

from __future__ import annotations

from typing import Any

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity


class RuleEngine:
    """
    Orchestrates rule execution and score aggregation.

    Features:
    - Execute all enabled rules
    - Aggregate scores with weights
    - Calculate composite risk
    - Generate combined explanations
    """

    def __init__(self):
        """Initialize rule engine."""
        self.rules: list[BaseRule] = []

    def register_rule(self, rule: BaseRule) -> None:
        """
        Register a rule with the engine.

        Args:
            rule: Rule instance to register
        """
        self.rules.append(rule)

    def register_rules(self, rules: list[BaseRule]) -> None:
        """
        Register multiple rules.

        Args:
            rules: List of rule instances
        """
        self.rules.extend(rules)

    def evaluate(
        self,
        transaction_data: dict[str, Any],
        features: dict[str, Any],
    ) -> tuple[float, list[RuleResult]]:
        """
        Evaluate all registered rules.

        Args:
            transaction_data: Raw transaction data
            features: Extracted features

        Returns:
            Tuple of (composite_score, rule_results)
        """
        rule_results = []
        total_score = 0.0
        total_weight = 0.0
        triggered_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                result = rule.evaluate(transaction_data, features)
                rule_results.append(result)

                # Weighted score aggregation
                weighted_score = result.score * rule.weight
                total_score += weighted_score
                total_weight += rule.weight

                if result.triggered:
                    triggered_rules.append(result)

            except Exception as e:
                # Log error but continue
                print(f"Rule evaluation error ({rule.rule_id}): {e}")

        # Normalize score to 0-1
        composite_score = total_score / total_weight if total_weight > 0 else 0.0
        composite_score = max(0.0, min(1.0, composite_score))

        # Add metadata to results
        rule_results.append(RuleResult(
            rule_id="__composite__",
            rule_name="Composite Risk Score",
            triggered=composite_score > 0.5,
            score=composite_score,
            severity=RuleSeverity.HIGH if composite_score > 0.8 else RuleSeverity.MEDIUM,
            explanation=f"{len(triggered_rules)} rules triggered out of {len(self.rules)}",
            metadata={
                "triggered_count": len(triggered_rules),
                "total_rules": len(self.rules),
                "triggered_rules": [r.rule_id for r in triggered_rules],
            },
        ))

        return composite_score, rule_results

    def get_triggered_rules(self, rule_results: list[RuleResult]) -> list[RuleResult]:
        """
        Get only triggered rules.

        Args:
            rule_results: All rule results

        Returns:
            List of triggered rule results
        """
        return [r for r in rule_results if r.triggered and not r.rule_id.startswith("__")]

    def get_rule_by_id(self, rule_id: str) -> BaseRule | None:
        """
        Get rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule instance or None
        """
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def get_enabled_rules(self) -> list[BaseRule]:
        """
        Get all enabled rules.

        Returns:
            List of enabled rules
        """
        return [rule for rule in self.rules if rule.enabled]
