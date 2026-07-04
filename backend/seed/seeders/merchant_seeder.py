"""
Seeder for merchant data. Generates 50+ realistic merchants.
"""

from seed.base import BaseSeeder
from seed.utils import fake, random_merchant_category, random_bangladesh_location, generate_merchant_code
from app.models.transaction.merchant import Merchant


MERCHANT_NAMES = [
    # Retail
    "Agora Superstore", "Shwapno", "Meena Bazar", "Unimart", "Priyo Shop",
    "Daraz Bangladesh", "Pickaboo", "Bagdoom", "Evaly", "Sheba.xyz",
    "Otobi", "Hatil", "Regal Furniture", "Brothers Furniture", "Partex",
    # Restaurant
    "KFC Bangladesh", "Pizza Hut", "Takeout", "Food Panda", "HungryNaki",
    "Haat Khola", "Star Kabab", "Sultan's Dine", "Woodhouse Grill", "Izumi",
    # E-commerce
    "ShopUp", "Chaldal", "Othoba", "AjkerDeal", "Kiksha",
    "Rokomari.com", "BoiBazar", "Jyoti Books", "Bindass", "PriyoCom",
    # Utilities
    "Desco", "DPDC", "WASA Dhaka", "Titas Gas", "BTCL",
    # Healthcare
    "Square Hospital", "Apollo Dhaka", "Labaid", "Ibn Sina", "Popular Hospital",
    "Green Life Hospital", "Ayesha Memorial", "Ad-din Hospital", "Shamorita", "Delta Hospital",
    # Telecom
    "Grameenphone", "Robi", "Banglalink", "Teletalk", "Airtel Bangladesh",
    # Travel
    "Biman Bangladesh", "US-Bangla Airlines", "Novoair", "Shohoz", "SR Travels",
    "S.A. Paribahan", "Hanif Enterprise", "Green Line", "Ena Transport", "BRTC",
    # Education
    "Udemy Bangladesh", "10 Minute School", "Shikho", "BBC Janala", "Byju's",
    "Oxford International", "British Council", "Daffodil International", "East West", "North South University",
    # Entertainment
    "Blockbuster BD", "Starf Cineplex", "Bioscope", "Chorki", "Hoichoi",
    "Gaming Zone BD", "Fitness Hub BD", "Bashundhara Concert", "Dhaka Club", "Senate Club",
]


class MerchantSeeder(BaseSeeder):
    """Seed merchant data."""

    async def seed(self) -> dict[str, int]:
        records = []
        for i, name in enumerate(MERCHANT_NAMES[:52]):
            category, subcategory = random_merchant_category()
            loc = random_bangladesh_location()
            risk_levels = ["low", "low", "low", "medium", "medium", "high"]
            records.append({
                "merchant_code": generate_merchant_code(category, i + 1),
                "merchant_name": name,
                "merchant_category": category,
                "business_type": subcategory,
                "risk_rating": fake.random_element(risk_levels),
                "status": "active",
                "email": fake.company_email(),
                "phone": fake.phone_number(),
                "website": f"https://{name.lower().replace(' ', '').replace('.', '')}.com",
                "is_active": True,
            })

        await self.bulk_insert(Merchant, records)
        self.add_stat("merchants", len(records))
        return self.get_stats()

    async def clear(self):
        await self.clear_table("merchants")