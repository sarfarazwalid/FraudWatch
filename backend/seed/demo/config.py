"""
Demo seed configuration and constants.

This module contains all configuration parameters for the demo data generation,
including user counts, transaction volumes, fraud scenarios, and other settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class DemoConfig:
    """Configuration for demo data generation."""

    # ── User Configuration ──
    NUM_SUPER_ADMINS: int = 1
    NUM_FRAUD_ANALYSTS: int = 5
    NUM_INVESTIGATORS: int = 4
    NUM_VIEWERS: int = 3
    TOTAL_USERS: int = 13  # Sum of above

    # ── Transaction Configuration ──
    NUM_TRANSACTIONS: int = 50000
    FRAUD_RATIO: float = 0.05  # 5% fraud
    LEGITIMATE_RATIO: float = 0.95  # 95% legitimate

    # ── Time Range ──
    TRANSACTION_DAYS_BACK: int = 90  # Generate transactions over last 90 days

    # ── Fraud Alert Configuration ──
    ALERT_RATIO_FROM_FRAUD: float = 0.50  # 50% of fraud transactions generate alerts
    ALERT_SEVERITY_DISTRIBUTION: Dict[str, float] = field(default_factory=lambda: {
        "critical": 0.10,  # 10%
        "high": 0.25,      # 25%
        "medium": 0.40,    # 40%
        "low": 0.25,       # 25%
    })

    # ── Fraud Case Configuration ──
    NUM_CASES_MIN: int = 300
    NUM_CASES_MAX: int = 500
    CASE_RATIO_FROM_ALERTS: float = 0.60  # 60% of alerts become cases

    # ── ML Model Configuration ──
    NUM_MODEL_VERSIONS: int = 6
    NUM_TRAINING_RUNS: int = 8
    NUM_PREDICTION_HISTORY: int = 50000  # One per transaction
    NUM_FEATURE_IMPORTANCE: int = 10  # Per model version

    # ── Analytics Configuration ──
    ANALYTICS_DAYS_BACK: int = 90  # 90 days of analytics data

    # ── Demo Credentials ──
    DEMO_USERS: List[Dict] = field(default_factory=lambda: [
        {
            "email": "admin@fraudwatch.demo",
            "password": "Admin@123",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin",
            "description": "Full system access"
        },
        {
            "email": "analyst@fraudwatch.demo",
            "password": "Analyst@123",
            "first_name": "John",
            "last_name": "Analyst",
            "role": "fraud_analyst",
            "description": "Fraud analysis and monitoring"
        },
        {
            "email": "investigator@fraudwatch.demo",
            "password": "Investigator@123",
            "first_name": "Sarah",
            "last_name": "Investigator",
            "role": "investigator",
            "description": "Case investigation and resolution"
        },
        {
            "email": "viewer@fraudwatch.demo",
            "password": "Viewer@123",
            "first_name": "Mike",
            "last_name": "Viewer",
            "role": "viewer",
            "description": "Read-only dashboard access"
        },
    ])

    # ── Fraud Scenario Types ──
    FRAUD_SCENARIOS: List[Dict] = field(default_factory=lambda: [
        {
            "name": "account_takeover",
            "weight": 0.20,
            "risk_score_range": (0.90, 0.98),
            "severity": "critical",
            "description": "Account takeover with new device and unusual location"
        },
        {
            "name": "transaction_velocity",
            "weight": 0.25,
            "risk_score_range": (0.85, 0.95),
            "severity": "high",
            "description": "Multiple rapid transactions from same device"
        },
        {
            "name": "suspicious_merchant",
            "weight": 0.15,
            "risk_score_range": (0.75, 0.90),
            "severity": "medium",
            "description": "New merchant with unusual category and high refund rate"
        },
        {
            "name": "location_anomaly",
            "weight": 0.20,
            "risk_score_range": (0.70, 0.85),
            "severity": "high",
            "description": "Impossible travel with foreign IP and VPN/proxy"
        },
        {
            "name": "high_value_fraud",
            "weight": 0.20,
            "risk_score_range": (0.80, 0.95),
            "severity": "critical",
            "description": "Unusually large amount to first-time recipient"
        },
    ])

    # ── ML Model Definitions ──
    ML_MODELS: List[Dict] = field(default_factory=lambda: [
        {
            "name": "Fraud Detection XGBoost",
            "algorithm": "xgboost",
            "framework": "xgboost",
            "versions": 3,
            "current_version": 3,
            "status": "production",
            "accuracy": 0.968,
            "precision": 0.945,
            "recall": 0.927,
            "f1_score": 0.936,
            "roc_auc": 0.982,
        },
        {
            "name": "Isolation Forest Anomaly",
            "algorithm": "isolation_forest",
            "framework": "scikit_learn",
            "versions": 2,
            "current_version": 2,
            "status": "production",
            "accuracy": 0.942,
            "precision": 0.918,
            "recall": 0.901,
            "f1_score": 0.909,
            "roc_auc": 0.961,
        },
        {
            "name": "Risk Classification Model",
            "algorithm": "random_forest",
            "framework": "scikit_learn",
            "versions": 4,
            "current_version": 4,
            "status": "production",
            "accuracy": 0.951,
            "precision": 0.932,
            "recall": 0.915,
            "f1_score": 0.923,
            "roc_auc": 0.975,
        },
        {
            "name": "Neural Network Fraud Detector",
            "algorithm": "deep_neural_network",
            "framework": "tensorflow",
            "versions": 2,
            "current_version": 2,
            "status": "staged",
            "accuracy": 0.958,
            "precision": 0.938,
            "recall": 0.921,
            "f1_score": 0.929,
            "roc_auc": 0.978,
        },
        {
            "name": "Behavioral Analytics Model",
            "algorithm": "gradient_boosting",
            "framework": "lightgbm",
            "versions": 1,
            "current_version": 1,
            "status": "production",
            "accuracy": 0.945,
            "precision": 0.920,
            "recall": 0.903,
            "f1_score": 0.911,
            "roc_auc": 0.965,
        },
        {
            "name": "Transaction Velocity Model",
            "algorithm": "lightgbm",
            "framework": "lightgbm",
            "versions": 2,
            "current_version": 2,
            "status": "production",
            "accuracy": 0.940,
            "precision": 0.915,
            "recall": 0.898,
            "f1_score": 0.906,
            "roc_auc": 0.958,
        },
    ])

    # ── Feature Importance (Top Features) ──
    TOP_FRAUD_FEATURES: List[Tuple[str, float]] = field(default_factory=lambda: [
        ("transaction_velocity", 0.28),
        ("device_trust_score", 0.22),
        ("location_anomaly_score", 0.18),
        ("transaction_amount", 0.15),
        ("merchant_risk_score", 0.08),
        ("time_since_last_transaction", 0.05),
        ("user_behavior_deviation", 0.02),
        ("payment_method_risk", 0.015),
        ("channel_risk", 0.01),
        ("historical_fraud_rate", 0.005),
    ])

    # ── Merchant Categories ──
    MERCHANT_CATEGORIES: List[Tuple[str, List[str]]] = field(default_factory=lambda: [
        ("Retail", ["Supermarket", "Department Store", "Clothing Boutique", "Electronics Store", "Furniture Store"]),
        ("Restaurant", ["Fast Food", "Fine Dining", "Cafe", "Bakery", "Street Food"]),
        ("E-commerce", ["Online Marketplace", "Digital Goods", "Subscription Service", "Dropshipping"]),
        ("Utilities", ["Electricity", "Water", "Gas", "Internet", "Telephone"]),
        ("Government", ["Tax Payment", "License Fee", "Municipal Services", "Court Fees"]),
        ("Healthcare", ["Hospital", "Pharmacy", "Clinic", "Diagnostic Center", "Dental"]),
        ("Education", ["University", "School", "Tutoring", "Online Course", "Training Center"]),
        ("Ride Sharing", ["Car Ride", "Bike Ride", "Rickshaw", "Car Rental", "Logistics"]),
        ("Telecom", ["Mobile Recharge", "Data Package", "Postpaid Bill", "Roaming"]),
        ("Travel", ["Airline", "Hotel", "Bus Ticket", "Train Ticket", "Travel Agency"]),
        ("Entertainment", ["Cinema", "Gaming", "Streaming", "Event Ticket", "Amusement Park"]),
        ("Financial", ["Insurance", "Loan Payment", "Investment", "Remittance", "Microfinance"]),
    ])

    # ── Device Types ──
    DEVICE_TYPES: List[Dict] = field(default_factory=lambda: [
        {"type": "mobile", "os": "Android 14", "browser": "Chrome Mobile", "models": ["Samsung Galaxy S24", "Xiaomi 14 Pro", "OnePlus 12", "Vivo X100", "Oppo Find X7"]},
        {"type": "mobile", "os": "iOS 18", "browser": "Safari Mobile", "models": ["iPhone 16 Pro", "iPhone 16", "iPhone 15 Pro", "iPhone 15"]},
        {"type": "desktop", "os": "Windows 11", "browser": "Chrome", "models": ["Dell XPS 15", "HP Spectre", "Lenovo ThinkPad", "ASUS ZenBook"]},
        {"type": "desktop", "os": "macOS 15", "browser": "Safari", "models": ["MacBook Pro 16", "MacBook Air M3", "iMac M3"]},
        {"type": "desktop", "os": "Linux Ubuntu 24.04", "browser": "Firefox", "models": ["Custom Desktop", "ThinkPad T14", "System76"]},
        {"type": "tablet", "os": "iPadOS 18", "browser": "Safari", "models": ["iPad Pro M4", "iPad Air M2", "iPad 10th Gen"]},
        {"type": "tablet", "os": "Android 14", "browser": "Chrome", "models": ["Samsung Galaxy Tab S9", "Xiaomi Pad 6", "Lenovo Tab P12"]},
    ])

    # ── Payment Methods ──
    PAYMENT_METHODS: List[Dict] = field(default_factory=lambda: [
        {"code": "bkash", "name": "bKash", "category": "mobile_wallet"},
        {"code": "nagad", "name": "Nagad", "category": "mobile_wallet"},
        {"code": "rocket", "name": "Rocket", "category": "mobile_wallet"},
        {"code": "upay", "name": "Upay", "category": "mobile_wallet"},
        {"code": "visa", "name": "Visa", "category": "card"},
        {"code": "mastercard", "name": "Mastercard", "category": "card"},
        {"code": "amex", "name": "American Express", "category": "card"},
        {"code": "npsb", "name": "NPSB", "category": "bank_transfer"},
        {"code": "rtgs", "name": "RTGS", "category": "bank_transfer"},
        {"code": "cash", "name": "Cash", "category": "cash"},
        {"code": "cod", "name": "Cash on Delivery", "category": "cash"},
        {"code": "crypto", "name": "Cryptocurrency", "category": "digital"},
    ])

    # ── Currencies ──
    CURRENCIES: List[Dict] = field(default_factory=lambda: [
        {"code": "BDT", "name": "Bangladeshi Taka", "symbol": "৳", "decimal_places": 2, "is_active": True},
        {"code": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2, "is_active": True},
        {"code": "EUR", "name": "Euro", "symbol": "€", "decimal_places": 2, "is_active": True},
        {"code": "GBP", "name": "British Pound", "symbol": "£", "decimal_places": 2, "is_active": True},
        {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "decimal_places": 2, "is_active": True},
        {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "decimal_places": 2, "is_active": True},
        {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "decimal_places": 2, "is_active": True},
        {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼", "decimal_places": 2, "is_active": True},
        {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ", "decimal_places": 2, "is_active": True},
        {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥", "decimal_places": 2, "is_active": True},
    ])

    # ── Transaction Types ──
    TRANSACTION_TYPES: List[Dict] = field(default_factory=lambda: [
        {"code": "payment", "name": "Payment", "description": "Standard payment transaction"},
        {"code": "transfer", "name": "Transfer", "description": "Fund transfer between accounts"},
        {"code": "withdrawal", "name": "Withdrawal", "description": "Cash withdrawal"},
        {"code": "deposit", "name": "Deposit", "description": "Cash deposit"},
        {"code": "refund", "name": "Refund", "description": "Transaction refund"},
        {"code": "reversal", "name": "Reversal", "description": "Transaction reversal"},
        {"code": "fee", "name": "Fee", "description": "Service fee charge"},
        {"code": "bill_payment", "name": "Bill Payment", "description": "Utility bill payment"},
        {"code": "mobile_recharge", "name": "Mobile Recharge", "description": "Mobile top-up"},
        {"code": "salary", "name": "Salary", "description": "Salary disbursement"},
    ])

    # ── Transaction Statuses ──
    TRANSACTION_STATUSES: List[Dict] = field(default_factory=lambda: [
        {"code": "pending", "name": "Pending", "description": "Transaction initiated, awaiting processing"},
        {"code": "processing", "name": "Processing", "description": "Transaction being processed"},
        {"code": "completed", "name": "Completed", "description": "Transaction completed successfully"},
        {"code": "failed", "name": "Failed", "description": "Transaction failed"},
        {"code": "flagged", "name": "Flagged", "description": "Transaction flagged for review"},
        {"code": "cancelled", "name": "Cancelled", "description": "Transaction cancelled by user"},
        {"code": "refunded", "name": "Refunded", "description": "Transaction refunded"},
        {"code": "reversed", "name": "Reversed", "description": "Transaction reversed"},
    ])

    # ── Risk Levels ──
    RISK_LEVELS: List[Dict] = field(default_factory=lambda: [
        {"code": "low", "name": "Low", "description": "Low risk transaction", "score_min": 0, "score_max": 20},
        {"code": "medium", "name": "Medium", "description": "Medium risk transaction", "score_min": 21, "score_max": 50},
        {"code": "high", "name": "High", "description": "High risk transaction", "score_min": 51, "score_max": 80},
        {"code": "critical", "name": "Critical", "description": "Critical risk transaction", "score_min": 81, "score_max": 100},
    ])


# Global config instance
config = DemoConfig()
