#!/usr/bin/env python3
"""
Convenience script to run FraudWatch demo data seeder.

Usage:
    python seed_demo.py                    # Seed demo data
    python seed_demo.py --reset            # Reset and seed
    python seed_demo.py verify             # Verify data
    python seed_demo.py reset              # Clear data
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from seed.demo.main import main

if __name__ == "__main__":
    asyncio.run(main())
