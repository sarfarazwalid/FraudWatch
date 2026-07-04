"""Model registry seeder - generates ML model metadata."""
import random
from seed.base import BaseSeeder
from app.models.ml.model_registry import ModelRegistry

class ModelRegistrySeeder(BaseSeeder):
    async def seed(self) -> dict[str, int]:
        records = []
        models = [
            ("fraud_detector_v2.4", "xgb", "v2.4.0", "production"),
            ("fraud_detector_v2.3", "xgb", "v2.3.0", "archived"),
            ("fraud_detector_v2.2", "xgb", "v2.2.0", "archived"),
            ("transaction_scorer", "rf", "v1.0.0", "production"),
            ("anomaly_detector", "isolation_forest", "v1.0.0", "staging"),
        ]
        for name, algo, ver, status in models:
            records.append({
                "model_name": name,
                "algorithm": algo,
                "version": ver,
                "status": status,
                "accuracy": random.uniform(0.92, 0.99),
                "is_active": True,
            })
        await self.bulk_insert(ModelRegistry, records)
        self.add_stat("model_registries", len(records))
        return self.get_stats()
    async def clear(self):
        await self.clear_table("model_registry")