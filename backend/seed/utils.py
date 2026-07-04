"""
Utility functions for the seeding framework.
"""

import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from faker import Faker

fake = Faker()
Faker.seed(42)

# ── Bangladesh Locations ──
BANGLADESH_DIVISIONS = [
    {"name": "Dhaka", "lat": 23.8103, "lng": 90.4125, "districts": ["Dhaka", "Gazipur", "Narayanganj", "Tangail", "Faridpur"]},
    {"name": "Chattogram", "lat": 22.3569, "lng": 91.7832, "districts": ["Chattogram", "Cox's Bazar", "Comilla", "Noakhali", "Brahmanbaria"]},
    {"name": "Khulna", "lat": 22.8456, "lng": 89.5403, "districts": ["Khulna", "Jessore", "Kushtia", "Satkhira", "Bagerhat"]},
    {"name": "Rajshahi", "lat": 24.3745, "lng": 88.6042, "districts": ["Rajshahi", "Bogra", "Pabna", "Sirajganj", "Natore"]},
    {"name": "Sylhet", "lat": 24.8949, "lng": 91.8687, "districts": ["Sylhet", "Moulvibazar", "Habiganj", "Sunamganj"]},
    {"name": "Barishal", "lat": 22.7010, "lng": 90.3535, "districts": ["Barishal", "Patuakhali", "Bhola", "Pirojpur"]},
    {"name": "Rangpur", "lat": 25.7439, "lng": 89.2752, "districts": ["Rangpur", "Dinajpur", "Kurigram", "Lalmonirhat", "Nilphamari"]},
    {"name": "Mymensingh", "lat": 24.7471, "lng": 90.4203, "districts": ["Mymensingh", "Jamalpur", "Netrokona", "Sherpur"]},
]

# ── Merchant Categories ──
MERCHANT_CATEGORIES = [
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
]

# ── Device Types ──
DEVICE_TEMPLATES = [
    {"type": "mobile", "os": "Android 14", "browser": "Chrome Mobile", "models": ["Samsung Galaxy S24", "Xiaomi 14 Pro", "OnePlus 12", "Vivo X100", "Oppo Find X7"]},
    {"type": "mobile", "os": "iOS 18", "browser": "Safari Mobile", "models": ["iPhone 16 Pro", "iPhone 16", "iPhone 15 Pro", "iPhone 15"]},
    {"type": "desktop", "os": "Windows 11", "browser": "Chrome", "models": ["Dell XPS 15", "HP Spectre", "Lenovo ThinkPad", "ASUS ZenBook"]},
    {"type": "desktop", "os": "macOS 15", "browser": "Safari", "models": ["MacBook Pro 16", "MacBook Air M3", "iMac M3"]},
    {"type": "desktop", "os": "Linux Ubuntu 24.04", "browser": "Firefox", "models": ["Custom Desktop", "ThinkPad T14", "System76"]},
    {"type": "tablet", "os": "iPadOS 18", "browser": "Safari", "models": ["iPad Pro M4", "iPad Air M2", "iPad 10th Gen"]},
    {"type": "tablet", "os": "Android 14", "browser": "Chrome", "models": ["Samsung Galaxy Tab S9", "Xiaomi Pad 6", "Lenovo Tab P12"]},
]

# ── Payment Methods ──
PAYMENT_METHODS = [
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
]

# ── Currencies ──
CURRENCIES = [
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
]

# ── Transaction Types ──
TRANSACTION_TYPES = [
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
]

# ── Transaction Statuses ──
TRANSACTION_STATUSES = [
    {"code": "pending", "name": "Pending", "description": "Transaction initiated, awaiting processing"},
    {"code": "processing", "name": "Processing", "description": "Transaction being processed"},
    {"code": "completed", "name": "Completed", "description": "Transaction completed successfully"},
    {"code": "failed", "name": "Failed", "description": "Transaction failed"},
    {"code": "flagged", "name": "Flagged", "description": "Transaction flagged for review"},
    {"code": "cancelled", "name": "Cancelled", "description": "Transaction cancelled by user"},
    {"code": "refunded", "name": "Refunded", "description": "Transaction refunded"},
    {"code": "reversed", "name": "Reversed", "description": "Transaction reversed"},
]

# ── Risk Levels ──
RISK_LEVELS = [
    {"code": "low", "name": "Low", "description": "Low risk transaction", "score_min": 0, "score_max": 20},
    {"code": "medium", "name": "Medium", "description": "Medium risk transaction", "score_min": 21, "score_max": 50},
    {"code": "high", "name": "High", "description": "High risk transaction", "score_min": 51, "score_max": 80},
    {"code": "critical", "name": "Critical", "description": "Critical risk transaction", "score_min": 81, "score_max": 100},
]

# ── Fraud Rules ──
FRAUD_RULES = [
    {"name": "Velocity Check", "description": "Detects rapid successive transactions", "severity": "high", "category": "velocity"},
    {"name": "Amount Threshold", "description": "Flags transactions above amount threshold", "severity": "medium", "category": "amount"},
    {"name": "Geographic Anomaly", "description": "Detects impossible travel patterns", "severity": "critical", "category": "geography"},
    {"name": "New Device", "description": "Flags transactions from unrecognized devices", "severity": "medium", "category": "device"},
    {"name": "Dormant Account", "description": "Flags activity on long-dormant accounts", "severity": "high", "category": "behavioral"},
    {"name": "Card Testing", "description": "Detects card testing attack patterns", "severity": "critical", "category": "attack"},
    {"name": "Round Amount", "description": "Flags round-number laundering patterns", "severity": "low", "category": "amount"},
    {"name": "Merchant Abuse", "description": "Detects merchant collusion patterns", "severity": "high", "category": "merchant"},
    {"name": "Synthetic Identity", "description": "Detects synthetic identity patterns", "severity": "critical", "category": "identity"},
    {"name": "Country Restriction", "description": "Flags transactions from restricted countries", "severity": "high", "category": "geography"},
]


def random_bangladesh_location() -> dict:
    """Generate a random Bangladesh location."""
    div = random.choice(BANGLADESH_DIVISIONS)
    district = random.choice(div["districts"])
    lat = div["lat"] + random.uniform(-0.5, 0.5)
    lng = div["lng"] + random.uniform(-0.5, 0.5)
    return {
        "division": div["name"],
        "district": district,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "country": "Bangladesh",
        "timezone": "Asia/Dhaka",
    }


def random_device() -> dict:
    """Generate a random device fingerprint."""
    template = random.choice(DEVICE_TEMPLATES)
    model = random.choice(template["models"])
    fingerprint = hashlib.sha256(f"{model}-{random.randint(10000, 99999)}".encode()).hexdigest()[:32]
    return {
        "device_fingerprint": fingerprint,
        "device_type": template["type"],
        "os": template["os"],
        "browser": template["browser"],
        "device_model": model,
        "is_mobile": template["type"] in ("mobile", "tablet"),
    }


def random_merchant_category() -> tuple[str, str]:
    """Get a random merchant category and subcategory."""
    cat = random.choice(MERCHANT_CATEGORIES)
    sub = random.choice(cat[1])
    return cat[0], sub


def random_amount(min_val: float = 10, max_val: float = 50000, distribution: str = "normal") -> float:
    """Generate a random transaction amount with realistic distribution."""
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


def random_timestamp(start_days_ago: int = 90) -> datetime:
    """Generate a random timestamp within the last N days."""
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow()
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))


def random_phone() -> str:
    """Generate a Bangladesh phone number."""
    prefixes = ["017", "018", "019", "016", "015", "013", "014"]
    return f"+880{random.choice(prefixes)}{random.randint(10000000, 99999999)}"


def generate_email(first_name: str, last_name: str, domain: Optional[str] = None) -> str:
    """Generate a realistic email."""
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


def generate_transaction_ref(index: int) -> str:
    """Generate a transaction reference."""
    return f"TXN-{index:08d}"


def get_fraud_pattern(transaction: dict, fraud_type: str) -> dict:
    """Generate fraud metadata for a transaction."""
    patterns = {
        "velocity": {"pattern": "velocity_attack", "confidence": random.uniform(0.7, 0.95), "details": "Multiple rapid transactions detected"},
        "impossible_travel": {"pattern": "impossible_travel", "confidence": random.uniform(0.8, 0.98), "details": "Geographic distance impossible in time window"},
        "high_value": {"pattern": "high_value_transfer", "confidence": random.uniform(0.6, 0.9), "details": "Transaction exceeds typical user pattern"},
        "new_device": {"pattern": "new_device_anomaly", "confidence": random.uniform(0.5, 0.85), "details": "Transaction from unrecognized device"},
        "dormant": {"pattern": "dormant_account", "confidence": random.uniform(0.7, 0.95), "details": "Account inactive for extended period"},
        "round_amount": {"pattern": "round_number_laundering", "confidence": random.uniform(0.4, 0.7), "details": "Suspicious round-number transaction"},
        "card_testing": {"pattern": "card_testing", "confidence": random.uniform(0.8, 0.99), "details": "Multiple small transactions pattern detected"},
        "merchant_abuse": {"pattern": "merchant_abuse", "confidence": random.uniform(0.6, 0.9), "details": "Unusual merchant transaction pattern"},
        "synthetic": {"pattern": "synthetic_identity", "confidence": random.uniform(0.5, 0.8), "details": "Potential synthetic identity behavior"},
    }
    return patterns.get(fraud_type, {"pattern": "unknown", "confidence": 0.5, "details": "Anomalous pattern detected"})