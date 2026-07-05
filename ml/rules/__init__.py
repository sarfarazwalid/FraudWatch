"""
Fraud Rule Engine Module.

Pluggable rule-based fraud detection system.
Each rule is independent, configurable, and contributes to the final risk score.

Architecture:
- BaseRule: Abstract rule interface
- RuleEngine: Rule orchestration and execution
- RuleRegistry: Rule registration and management
- RuleLoader: Automatic rule loading
- Individual rule implementations (24 rules)
"""

from ml.rules.base_rule import BaseRule, RuleResult, RuleSeverity
from ml.rules.rule_engine import RuleEngine
from ml.rules.rule_registry import RuleRegistry
from ml.rules.rule_loader import load_all_rules

# Rule implementations
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

__all__ = [
    "BaseRule",
    "RuleResult",
    "RuleSeverity",
    "RuleEngine",
    "RuleRegistry",
    "load_all_rules",
    "HighAmountRule",
    "RapidTransactionRule",
    "ImpossibleTravelRule",
    "HighVelocityRule",
    "BlacklistedMerchantRule",
    "BlacklistedDeviceRule",
    "BlacklistedIPRule",
    "NightTransactionRule",
    "WeekendTransactionRule",
    "DormantAccountRule",
    "HighRiskCustomerRule",
    "NewCustomerRule",
    "UnusualSpendingRule",
    "NewDeviceRule",
    "DeviceCountryMismatchRule",
    "MultipleFailedAttemptsRule",
    "HighRiskMerchantRule",
    "UnverifiedMerchantRule",
    "RoundAmountRule",
    "CardTestingRule",
    "SyntheticIdentityRule",
    "UnusualTransactionTypeRule",
    "CurrencyMismatchRule",
    "CountryMismatchRule",
]
