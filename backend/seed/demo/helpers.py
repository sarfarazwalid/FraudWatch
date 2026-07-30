"""
Helper functions for demo data generation.

This module provides utility functions for generating realistic demo data,
including references, timestamps, and other common patterns.
"""

import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


def generate_transaction_reference(index: int) -> str:
    """Generate a unique transaction reference."""
    return f"TXN-{index:08d}"


def generate_alert_number(index: int) -> str:
    """Generate a unique alert number."""
    return f"ALT-{index:06d}"


def generate_case_number(index: int) -> str:
    """Generate a unique case number."""
    return f"CAS-{index:06d}"


def generate_prediction_id(index: int) -> str:
    """Generate a unique prediction ID."""
    return f"PRED-{index:08d}"


def random_timestamp(start_days_ago: int = 90, end_days_ago: int = 0) -> datetime:
    """
    Generate a random timestamp within a date range.

    Args:
        start_days_ago: Start of range (days ago from now)
        end_days_ago: End of range (days ago from now)

    Returns:
        Random datetime in UTC
    """
    start = datetime.now(timezone.utc) - timedelta(days=start_days_ago)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def random_amount(min_val: float = 10, max_val: float = 50000, distribution: str = "normal") -> float:
    """
    Generate a random transaction amount with realistic distribution.

    Args:
        min_val: Minimum amount
        max_val: Maximum amount
        distribution: Distribution type (normal, small, medium, large, round)

    Returns:
        Random amount rounded to 2 decimal places
    """
    if distribution == "small":
        return round(random.uniform(10, 500), 2)
    elif distribution == "medium":
        return round(random.uniform(500, 5000), 2)
    elif distribution == "large":
        return round(random.uniform(5000, 50000), 2)
    elif distribution == "round":
        return round(random.uniform(1000, 100000) / 1000, 0) * 1000
    else:
        # Normal-ish distribution favoring small amounts
        r = random.random()
        if r < 0.6:
            return round(random.uniform(10, 1000), 2)
        elif r < 0.85:
            return round(random.uniform(1000, 10000), 2)
        elif r < 0.95:
            return round(random.uniform(10000, 50000), 2)
        else:
            return round(random.uniform(50000, 200000), 2)


def random_phone() -> str:
    """Generate a Bangladesh phone number."""
    prefixes = ["017", "018", "019", "016", "015", "013", "014"]
    return f"+880{random.choice(prefixes)}{random.randint(10000000, 99999999)}"


def generate_email(first_name: str, last_name: str, domain: Optional[str] = None) -> str:
    """Generate a realistic email address."""
    if domain:
        return f"{first_name.lower()}.{last_name.lower()}@{domain}"
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me"]
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"


def generate_merchant_code(category: str, index: int) -> str:
    """Generate a merchant code."""
    prefix = category[:3].upper()
    return f"MER-{prefix}-{index:04d}"


def generate_agent_code(index: int) -> str:
    """Generate an agent code."""
    return f"AGT-{index:05d}"


def hash_string(text: str) -> str:
    """Generate SHA256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def weighted_choice(choices: List[Dict[str, Any]], weight_key: str = "weight") -> Any:
    """
    Make a weighted random choice from a list of options.

    Args:
        choices: List of dictionaries with weight values
        weight_key: Key containing the weight value

    Returns:
        Selected choice dictionary
    """
    total = sum(choice.get(weight_key, 1) for choice in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice in choices:
        weight = choice.get(weight_key, 1)
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[-1]


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def generate_device_fingerprint(model: str) -> str:
    """Generate a unique device fingerprint."""
    unique_id = random.randint(10000, 99999)
    return hashlib.sha256(f"{model}-{unique_id}".encode()).hexdigest()[:32]


def generate_external_reference(index: int) -> str:
    """Generate an external system reference."""
    systems = ["CORE", "SWITCH", "WALLET", "GATEWAY", "BILLPAY"]
    system = random.choice(systems)
    return f"{system}-{random.randint(100000, 999999)}"


def calculate_risk_level(score: float) -> str:
    """
    Calculate risk level from score.

    Args:
        score: Risk score (0-100)

    Returns:
        Risk level string (low, medium, high, critical)
    """
    if score <= 20:
        return "low"
    elif score <= 50:
        return "medium"
    elif score <= 80:
        return "high"
    else:
        return "critical"


def generate_feature_vector() -> Dict[str, float]:
    """Generate a random feature vector for ML predictions."""
    return {
        "amount_score": random.uniform(0, 1),
        "velocity_score": random.uniform(0, 1),
        "device_score": random.uniform(0, 1),
        "location_score": random.uniform(0, 1),
        "merchant_score": random.uniform(0, 1),
        "time_score": random.uniform(0, 1),
        "behavior_score": random.uniform(0, 1),
    }


def generate_transaction_metadata(is_fraud: bool = False, fraud_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate transaction metadata.

    Args:
        is_fraud: Whether this is a fraudulent transaction
        fraud_type: Type of fraud if applicable

    Returns:
        Metadata dictionary
    """
    metadata = {
        "ip_address": fake.ipv4() if random.random() > 0.3 else None,
        "user_agent": fake.user_agent() if random.random() > 0.3 else None,
        "session_id": fake.uuid4() if random.random() > 0.3 else None,
        "device_trusted": random.random() > 0.3,
        "vpn_detected": random.random() < 0.1,
        "proxy_detected": random.random() < 0.05,
    }

    if is_fraud and fraud_type:
        metadata["fraud_pattern"] = fraud_type
        metadata["fraud_confidence"] = round(random.uniform(0.7, 0.99), 2)
        metadata["triggered_rules"] = random.sample([
            "velocity_check",
            "amount_threshold",
            "geographic_anomaly",
            "new_device",
            "dormant_account",
        ], k=random.randint(1, 3))

    return metadata


def generate_evidence_json(fraud_type: str) -> Dict[str, Any]:
    """
    Generate evidence JSON for fraud cases.

    Args:
        fraud_type: Type of fraud

    Returns:
        Evidence dictionary
    """
    evidence = {
        "fraud_type": fraud_type,
        "detection_timestamp": datetime.now(timezone.utc).isoformat(),
        "automated_analysis": True,
    }

    # Add type-specific evidence
    if fraud_type == "account_takeover":
        evidence.update({
            "device_change": True,
            "location_change": True,
            "password_change": random.random() > 0.5,
            "failed_login_attempts": random.randint(3, 10),
        })
    elif fraud_type == "transaction_velocity":
        evidence.update({
            "velocity_anomaly": True,
            "transactions_in_5min": random.randint(5, 20),
            "amount_variance": round(random.uniform(0.5, 2.0), 2),
        })
    elif fraud_type == "suspicious_merchant":
        evidence.update({
            "new_merchant": True,
            "unusual_category": True,
            "high_refund_rate": True,
            "merchant_age_days": random.randint(1, 30),
        })
    elif fraud_type == "location_anomaly":
        evidence.update({
            "impossible_travel": True,
            "distance_km": random.randint(500, 5000),
            "time_window_hours": random.uniform(1, 6),
            "vpn_detected": True,
        })
    elif fraud_type == "high_value_fraud":
        evidence.update({
            "large_transaction": True,
            "first_time_recipient": True,
            "amount_multiplier": round(random.uniform(5, 20), 1),
            "unusual_time": random.random() > 0.5,
        })

    return evidence
