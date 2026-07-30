"""
Demo transaction generation module.

This module creates realistic fintech transaction data for the FraudWatch platform,
including both legitimate and fraudulent transactions with proper distributions.
Uses direct SQL INSERTs to avoid model/DB schema mismatches.
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from seed.demo.config import config
from seed.demo.helpers import (
    random_timestamp, random_amount, generate_transaction_reference,
    generate_external_reference, generate_transaction_metadata,
    calculate_risk_level, generate_feature_vector
)

logger = logging.getLogger(__name__)


async def create_transactions(session: AsyncSession) -> int:
    """Create demo transactions using direct SQL."""
    from uuid import uuid4

    logger.info("Creating demo transactions using direct SQL...")

    # First, ensure reference data exists
    await _ensure_reference_data(session)

    # Get reference data IDs
    refs = await _get_reference_ids(session)

    num_fraud = int(config.NUM_TRANSACTIONS * config.FRAUD_RATIO)
    num_legitimate = config.NUM_TRANSACTIONS - num_fraud

    logger.info(f"Generating {num_legitimate} legitimate and {num_fraud} fraudulent transactions")

    # Build fraud scenarios list with weights
    fraud_scenarios = []
    for scenario in config.FRAUD_SCENARIOS:
        count = int(num_fraud * scenario["weight"])
        fraud_scenarios.extend([scenario] * count)
    random.shuffle(fraud_scenarios)

    channels = ['mobile_app', 'web', 'api', 'pos', 'atm']
    sources = ['core_banking', 'switch', 'wallet', 'payment_gateway']

    BATCH_SIZE = 5000
    total_created = 0

    for batch_start in range(0, config.NUM_TRANSACTIONS, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, config.NUM_TRANSACTIONS)
        values = []
        params = {}

        for i in range(batch_start, batch_end):
            idx = i + 1
            is_fraud = (i >= num_legitimate)

            if is_fraud:
                scenario_idx = (i - num_legitimate) % len(fraud_scenarios)
                scenario = fraud_scenarios[scenario_idx]
                risk_score = int(random.uniform(*scenario["risk_score_range"]) * 10)  # 0-1000 scale

                if scenario["name"] == "high_value_fraud":
                    amount = round(random.uniform(50000, 500000), 2)
                elif scenario["name"] == "transaction_velocity":
                    amount = round(random.uniform(100, 5000), 2)
                else:
                    amount = round(random.uniform(1000, 100000), 2)
            else:
                risk_score = int(random.uniform(0, 25) * 10)  # 0-250 on 0-1000 scale
                amount = round(random.uniform(10, 10000), 2)

            tx_ref = generate_transaction_reference(idx)
            ext_ref = generate_external_reference(idx)
            sender = f"sender_{random.randint(100000, 999999)}"
            receiver = f"receiver_{random.randint(100000, 999999)}"
            fee = round(amount * random.uniform(0.01, 0.03), 2)
            net_amount = round(amount - fee, 2)
            timestamp = random_timestamp(start_days_ago=90, end_days_ago=0)
            channel = random.choice(channels)
            source = random.choice(sources)
            risk_level = calculate_risk_level(risk_score / 10)  # convert back for helper
            risk_level_id = refs["risk_levels"].get(risk_level)
            currency_id = random.choice(refs["currencies"])
            payment_method_id = random.choice(refs["payment_methods"])
            transaction_type_id = random.choice(refs["transaction_types"])
            status_id = random.choice(refs["statuses"])
            description = "Legitimate transaction" if not is_fraud else f"Transaction - {scenario['description']}" if is_fraud else "Transaction"

            tid = uuid4()

            values.append(
                f"(:id_{idx}, :tx_ref_{idx}, :ext_ref_{idx}, :sender_{idx}, :receiver_{idx}, "
                f":amt_{idx}, :fee_{idx}, :net_{idx}, :currency_{idx}, :pm_{idx}, :tt_{idx}, "
                f":status_{idx}, :risk_level_{idx}, :channel_{idx}, :source_{idx}, :ts_{idx}, "
                f":risk_score_{idx}, :desc_{idx}, :created_{idx}, :updated_{idx})"
            )

            params.update({
                f"id_{idx}": tid,
                f"tx_ref_{idx}": tx_ref,
                f"ext_ref_{idx}": ext_ref,
                f"sender_{idx}": sender,
                f"receiver_{idx}": receiver,
                f"amt_{idx}": amount,
                f"fee_{idx}": fee,
                f"net_{idx}": net_amount,
                f"currency_{idx}": currency_id,
                f"pm_{idx}": payment_method_id,
                f"tt_{idx}": transaction_type_id,
                f"status_{idx}": status_id,
                f"risk_level_{idx}": risk_level_id,
                f"channel_{idx}": channel,
                f"source_{idx}": source,
                f"ts_{idx}": timestamp,
                f"risk_score_{idx}": risk_score,
                f"desc_{idx}": description,
                f"created_{idx}": datetime.now(timezone.utc),
                f"updated_{idx}": datetime.now(timezone.utc),
            })

        # Insert batch
        insert_sql = f"""
            INSERT INTO transactions (
                id, transaction_reference, external_reference,
                sender_identifier, receiver_identifier,
                amount, fee, net_amount,
                currency_id, payment_method_id, transaction_type_id,
                status_id, risk_level_id,
                channel, source_system,
                transaction_timestamp,
                risk_score,
                description,
                created_at, updated_at, version
            ) VALUES {','.join(values)}
            ON CONFLICT (id) DO NOTHING
        """

        await session.execute(text(insert_sql), params)
        await session.flush()
        total_created += (batch_end - batch_start)
        logger.info(f"Created {total_created}/{config.NUM_TRANSACTIONS} transactions")

    logger.info(f"Created {total_created} total transactions")
    return total_created


async def _ensure_reference_data(session: AsyncSession) -> None:
    """Ensure reference data exists in the database."""
    from uuid import uuid4

    # Currencies
    result = await session.execute(text("SELECT COUNT(*) FROM currencies"))
    if result.scalar() == 0:
        for code, name, symbol in [("USD","US Dollar","$"),("EUR","Euro","€"),("GBP","British Pound","£")]:
            await session.execute(text("""
                INSERT INTO currencies (id, code, name, symbol, decimal_places, is_active, version)
                VALUES (:id, :code, :name, :symbol, 2, true, 1) ON CONFLICT (code) DO NOTHING
            """), {"id": uuid4(), "code": code, "name": name, "symbol": symbol})

    # Payment methods
    result = await session.execute(text("SELECT COUNT(*) FROM payment_methods"))
    if result.scalar() == 0:
        for name, pmtype in [("Credit Card","card"),("Debit Card","card"),("Bank Transfer","bank_transfer"),("Digital Wallet","mobile_money")]:
            await session.execute(text("""
                INSERT INTO payment_methods (id, name, payment_method_type, is_active, version)
                VALUES (:id, :name, :pmtype, true, 1) ON CONFLICT (name) DO NOTHING
            """), {"id": uuid4(), "name": name, "pmtype": pmtype})

    # Transaction types
    result = await session.execute(text("SELECT COUNT(*) FROM transaction_types"))
    if result.scalar() == 0:
        for name, desc, tx_type, is_debit in [("payment","Payment","payment",False),("transfer","Transfer","transfer",False),("withdrawal","Withdrawal","withdrawal",True),("refund","Refund","refund",False)]:
            await session.execute(text("""
                INSERT INTO transaction_types (id, name, description, transaction_type, is_debit, version)
                VALUES (:id, :name, :desc, :tx_type, :is_debit, 1) ON CONFLICT (name) DO NOTHING
            """), {"id": uuid4(), "name": name, "desc": desc, "tx_type": tx_type, "is_debit": is_debit})

    # Transaction statuses
    result = await session.execute(text("SELECT COUNT(*) FROM transaction_statuses"))
    if result.scalar() == 0:
        for status_value, name in [("pending","Pending"),("completed","Completed"),("failed","Failed"),("flagged","Flagged")]:
            await session.execute(text("""
                INSERT INTO transaction_statuses (id, status_value, name, version)
                VALUES (:id, :status_value, :name, 1) ON CONFLICT (status_value) DO NOTHING
            """), {"id": uuid4(), "status_value": status_value, "name": name})

    # Risk levels
    result = await session.execute(text("SELECT COUNT(*) FROM risk_levels"))
    if result.scalar() == 0:
        for risk_level, name, score_min, score_max in [("low","Low",0,200),("medium","Medium",201,500),("high","High",501,800),("critical","Critical",801,1000)]:
            await session.execute(text("""
                INSERT INTO risk_levels (id, risk_level, name, score_min, score_max, version)
                VALUES (:id, :risk_level, :name, :score_min, :score_max, 1) ON CONFLICT (risk_level) DO NOTHING
            """), {"id": uuid4(), "risk_level": risk_level, "name": name, "score_min": score_min, "score_max": score_max})

    await session.flush()


async def _get_reference_ids(session: AsyncSession) -> Dict[str, Any]:
    """Get reference data IDs."""
    result = await session.execute(text("SELECT id FROM currencies LIMIT 10"))
    currencies = [r[0] for r in result.fetchall()]

    result = await session.execute(text("SELECT id FROM payment_methods LIMIT 10"))
    payment_methods = [r[0] for r in result.fetchall()]

    result = await session.execute(text("SELECT id FROM transaction_types LIMIT 10"))
    transaction_types = [r[0] for r in result.fetchall()]

    result = await session.execute(text("SELECT id FROM transaction_statuses LIMIT 10"))
    statuses = [r[0] for r in result.fetchall()]

    result = await session.execute(text("SELECT id, risk_level FROM risk_levels LIMIT 10"))
    risk_levels = {r[1]: r[0] for r in result.fetchall()}

    return {
        "currencies": currencies,
        "payment_methods": payment_methods,
        "transaction_types": transaction_types,
        "statuses": statuses,
        "risk_levels": risk_levels,
    }
