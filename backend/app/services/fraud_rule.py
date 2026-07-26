"""
FraudRule service.

Handles fraud rule management business logic and rule evaluation engine.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.fraud.fraud_rule import FraudRule
from app.models.transaction.transaction import Transaction
from app.repositories.fraud_rule import FraudRuleRepository
from app.schemas.fraud import RuleEvaluationResult, RuleEvaluationResponse

logger = logging.getLogger(__name__)


class FraudRuleService:
    """
    Service for fraud rule operations and transaction evaluation.

    Handles rule creation, updates, retrieval, and real-time
    transaction evaluation against active rules.
    """

    def __init__(self, fraud_rule_repo: Optional[FraudRuleRepository] = None, session: Optional[AsyncSession] = None):
        self.fraud_rule_repo = fraud_rule_repo
        self.session = session or (fraud_rule_repo.session if fraud_rule_repo else None)

    async def create_rule(self, rule_data: dict) -> FraudRule:
        """
        Create a new fraud rule.

        Args:
            rule_data: Rule creation data

        Returns:
            Created rule
        """
        rule = FraudRule(**rule_data)
        self.fraud_rule_repo.session.add(rule)
        await self.fraud_rule_repo.session.flush()
        await self.fraud_rule_repo.session.refresh(rule)
        return rule

    async def get_rule(self, rule_id: str) -> Optional[FraudRule]:
        """Get fraud rule by ID."""
        return await self.fraud_rule_repo.get(rule_id)

    async def get_rule_by_code(self, rule_code: str) -> Optional[FraudRule]:
        """Get fraud rule by rule code."""
        return await self.fraud_rule_repo.get_by_rule_code(rule_code)

    async def update_rule(self, rule_id: str, update_data: dict) -> Optional[FraudRule]:
        """Update fraud rule."""
        rule = await self.fraud_rule_repo.get(rule_id)
        if not rule:
            return None

        for field, value in update_data.items():
            if hasattr(rule, field) and value is not None:
                setattr(rule, field, value)

        await self.fraud_rule_repo.session.flush()
        await self.fraud_rule_repo.session.refresh(rule)
        return rule

    async def get_active_rules(self, skip: int = 0, limit: int = 100) -> List[FraudRule]:
        """Get all active rules."""
        return await self.fraud_rule_repo.get_active_rules(skip, limit)

    async def get_rules_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[FraudRule]:
        """Get rules by category."""
        return await self.fraud_rule_repo.get_rules_by_category(category, skip, limit)

    async def evaluate_transaction(
        self,
        transaction: Transaction,
        features: Dict[str, Any],
    ) -> RuleEvaluationResponse:
        """
        Evaluate a transaction against all active fraud rules.

        Rules evaluated:
        RULE 1 - High amount anomaly:
            IF amount > user_average * 5 → severity = HIGH

        RULE 2 - Velocity fraud:
            IF more than 10 transactions within 5 minutes → severity = CRITICAL

        RULE 3 - Suspicious location:
            IF VPN detected OR country risk high → severity = MEDIUM

        Args:
            transaction: The transaction to evaluate
            features: Extracted feature dictionary

        Returns:
            RuleEvaluationResponse with all rule results
        """
        results: List[RuleEvaluationResult] = []

        # RULE 1: High amount anomaly
        amount = float(transaction.amount)
        user_average = features.get("user_average_amount", 0.0)
        rule1_triggered = user_average > 0 and amount > user_average * 5
        results.append(RuleEvaluationResult(
            rule_name="high_amount_anomaly",
            triggered=rule1_triggered,
            severity="high" if rule1_triggered else "none",
            explanation=(
                f"Transaction amount ${amount:.2f} exceeds 5x user average "
                f"(${user_average:.2f})"
            ) if rule1_triggered else (
                f"Transaction amount ${amount:.2f} within normal range "
                f"(avg: ${user_average:.2f})"
            ),
        ))

        # RULE 2: Velocity fraud
        recent_count = features.get("recent_transaction_count", 0)
        rule2_triggered = recent_count > 10
        results.append(RuleEvaluationResult(
            rule_name="velocity_fraud",
            triggered=rule2_triggered,
            severity="critical" if rule2_triggered else "none",
            explanation=(
                f"{recent_count} transactions detected within 5 minutes "
                f"(threshold: 10)"
            ) if rule2_triggered else (
                f"{recent_count} transactions within 5 minutes (normal)"
            ),
        ))

        # RULE 3: Suspicious location
        vpn_detected = features.get("vpn_detected", False)
        country_risk_high = features.get("country_risk_high", False)
        rule3_triggered = vpn_detected or country_risk_high
        reasons = []
        if vpn_detected:
            reasons.append("VPN/proxy detected")
        if country_risk_high:
            reasons.append("High-risk country")
        results.append(RuleEvaluationResult(
            rule_name="suspicious_location",
            triggered=rule3_triggered,
            severity="medium" if rule3_triggered else "none",
            explanation="; ".join(reasons) if reasons else "Location appears normal",
        ))

        # Calculate triggered count and max severity
        triggered_count = sum(1 for r in results if r.triggered)
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        max_severity = "none"
        max_sev_val = 0
        for r in results:
            sev_val = severity_order.get(r.severity, 0)
            if sev_val > max_sev_val:
                max_sev_val = sev_val
                max_severity = r.severity

        return RuleEvaluationResponse(
            rules=results,
            total_rules=len(results),
            triggered_count=triggered_count,
            max_severity=max_severity,
        )
