"""
Rule loader for automatic rule registration.

Loads and registers all fraud detection rules.
"""

from __future__ import annotations

from ml.rules.base_rule import BaseRule
from ml.rules.rule_registry import RuleRegistry
from ml.rules.high_amount_rule import HighAmountRule
from ml.rules.velocity_rules import RapidTransactionRule, ImpossibleTravelRule, HighVelocityRule
from ml.rules.blacklist_rules import BlacklistedMerchantRule, BlacklistedDeviceRule, BlacklistedIPRule
from ml.rules.temporal_rules import NightTransactionRule, WeekendTransactionRule, DormantAccountRule
from ml.rules.risk_rules import HighRiskCustomerRule, NewCustomerRule, UnusualSpendingRule
from ml.rules.device_rules import NewDeviceRule, DeviceCountryMismatchRule, MultipleFailedAttemptsRule
from ml.rules.merchant_rules import HighRiskMerchantRule, UnverifiedMerchantRule, RoundAmountRule
from ml.rules.transaction_pattern_rules import (
    CardTestingRule,
    SyntheticIdentityRule,
    UnusualTransactionTypeRule,
    CurrencyMismatchRule,
    CountryMismatchRule,
)


def load_all_rules() -> RuleRegistry:
    """
    Load and register all fraud detection rules.

    Returns:
        RuleRegistry with all rules registered
    """
    registry = RuleRegistry()

    # Register all rules
    rules: list[BaseRule] = [
        # High amount
        HighAmountRule(),
        # Velocity
        RapidTransactionRule(),
        ImpossibleTravelRule(),
        HighVelocityRule(),
        # Blacklist
        BlacklistedMerchantRule(),
        BlacklistedDeviceRule(),
        BlacklistedIPRule(),
        # Temporal
        NightTransactionRule(),
        WeekendTransactionRule(),
        DormantAccountRule(),
        # Risk
        HighRiskCustomerRule(),
        NewCustomerRule(),
        UnusualSpendingRule(),
        # Device
        NewDeviceRule(),
        DeviceCountryMismatchRule(),
        MultipleFailedAttemptsRule(),
        # Merchant
        HighRiskMerchantRule(),
        UnverifiedMerchantRule(),
        RoundAmountRule(),
        # Transaction patterns
        CardTestingRule(),
        SyntheticIdentityRule(),
        UnusualTransactionTypeRule(),
        CurrencyMismatchRule(),
        CountryMismatchRule(),
    ]

    for rule in rules:
        registry.register(rule)

    return registry
