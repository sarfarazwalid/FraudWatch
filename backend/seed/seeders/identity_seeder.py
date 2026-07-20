"""
Seeder for identity data: roles, permissions, users.
"""

import random
import bcrypt
from uuid import uuid4
from seed.base import BaseSeeder
from seed.utils import fake, generate_email, random_phone
from app.models.identity.role import Role
from app.models.identity.permission import Permission
from app.models.identity.role_permission import RolePermission
from app.models.identity.user import User
from app.models.enums import RoleType, UserStatus

# Default password for all seeded users (hashed)
DEFAULT_PASSWORD = bcrypt.hashpw("FraudWatch@2024".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# ── Roles ──
ROLES = [
    {"name": "super_admin", "description": "Full system access with all permissions", "role_type": RoleType.SUPER_ADMIN, "is_system": True},
    {"name": "admin", "description": "Administrative access with most permissions", "role_type": RoleType.ADMIN, "is_system": True},
    {"name": "fraud_analyst", "description": "Fraud analysis and investigation access", "role_type": RoleType.FRAUD_ANALYST, "is_system": True},
    {"name": "compliance_officer", "description": "Compliance and reporting access", "role_type": RoleType.COMPLIANCE_OFFICER, "is_system": True},
    {"name": "viewer", "description": "Read-only access to dashboards and reports", "role_type": RoleType.VIEWER, "is_system": True},
]

# ── Permissions ──
PERMISSIONS = [
    # Transaction permissions
    {"name": "transaction:read", "description": "View transactions", "resource": "transaction", "action": "read"},
    {"name": "transaction:create", "description": "Create transactions", "resource": "transaction", "action": "create"},
    {"name": "transaction:update", "description": "Update transactions", "resource": "transaction", "action": "update"},
    {"name": "transaction:delete", "description": "Delete transactions", "resource": "transaction", "action": "delete"},
    {"name": "transaction:approve", "description": "Approve flagged transactions", "resource": "transaction", "action": "approve"},
    {"name": "transaction:refund", "description": "Process refunds", "resource": "transaction", "action": "refund"},
    # Fraud permissions
    {"name": "fraud:read", "description": "View fraud alerts", "resource": "fraud", "action": "read"},
    {"name": "fraud:create", "description": "Create fraud alerts", "resource": "fraud", "action": "create"},
    {"name": "fraud:update", "description": "Update fraud alerts", "resource": "fraud", "action": "update"},
    {"name": "fraud:resolve", "description": "Resolve fraud cases", "resource": "fraud", "action": "resolve"},
    {"name": "fraud:rules", "description": "Manage fraud detection rules", "resource": "fraud", "action": "rules"},
    # Investigation permissions
    {"name": "investigation:read", "description": "View investigations", "resource": "investigation", "action": "read"},
    {"name": "investigation:create", "description": "Create investigations", "resource": "investigation", "action": "create"},
    {"name": "investigation:update", "description": "Update investigations", "resource": "investigation", "action": "update"},
    {"name": "investigation:close", "description": "Close investigations", "resource": "investigation", "action": "close"},
    # User management
    {"name": "user:read", "description": "View users", "resource": "user", "action": "read"},
    {"name": "user:create", "description": "Create users", "resource": "user", "action": "create"},
    {"name": "user:update", "description": "Update users", "resource": "user", "action": "update"},
    {"name": "user:delete", "description": "Delete users", "resource": "user", "action": "delete"},
    {"name": "user:roles", "description": "Manage user roles", "resource": "user", "action": "roles"},
    # Analytics permissions
    {"name": "analytics:read", "description": "View analytics", "resource": "analytics", "action": "read"},
    {"name": "analytics:export", "description": "Export analytics data", "resource": "analytics", "action": "export"},
    # ML permissions
    {"name": "ml:read", "description": "View ML models", "resource": "ml", "action": "read"},
    {"name": "ml:train", "description": "Train ML models", "resource": "ml", "action": "train"},
    {"name": "ml:deploy", "description": "Deploy ML models", "resource": "ml", "action": "deploy"},
    # Settings permissions
    {"name": "settings:read", "description": "View settings", "resource": "settings", "action": "read"},
    {"name": "settings:update", "description": "Update settings", "resource": "settings", "action": "update"},
    {"name": "settings:audit", "description": "View audit logs", "resource": "settings", "action": "audit"},
]

# ── Role-Permission Mapping ──
ROLE_PERMISSIONS = {
    "super_admin": [p["name"] for p in PERMISSIONS],
    "admin": [p["name"] for p in PERMISSIONS if p["action"] not in ("delete",)],
    "fraud_analyst": [p["name"] for p in PERMISSIONS if p["resource"] in ("transaction", "fraud", "investigation", "analytics")],
    "compliance_officer": [p["name"] for p in PERMISSIONS if p["resource"] in ("transaction", "fraud", "analytics", "settings")],
    "viewer": [p["name"] for p in PERMISSIONS if p["action"] == "read"],
}

# ── Admin Users ──
ADMIN_USERS = [
    {"email": "admin@fraudwatch.com", "first_name": "System", "last_name": "Admin", "role": "super_admin", "status": UserStatus.ACTIVE},
    {"email": "analyst@fraudwatch.com", "first_name": "Sarah", "last_name": "Chen", "role": "fraud_analyst", "status": UserStatus.ACTIVE},
    {"email": "compliance@fraudwatch.com", "first_name": "James", "last_name": "Wilson", "role": "compliance_officer", "status": UserStatus.ACTIVE},
    {"email": "risk@fraudwatch.com", "first_name": "Maria", "last_name": "Garcia", "role": "fraud_analyst", "status": UserStatus.ACTIVE},
    {"email": "support@fraudwatch.com", "first_name": "Alex", "last_name": "Thompson", "role": "viewer", "status": UserStatus.ACTIVE},
]

# ── Demo Customer Accounts ──
DEMO_CUSTOMERS = [
    {"first_name": "Rafiq", "last_name": "Hossain", "gender": "male"},
    {"first_name": "Fatima", "last_name": "Begum", "gender": "female"},
    {"first_name": "Kamal", "last_name": "Ahmed", "gender": "male"},
    {"first_name": "Nasrin", "last_name": "Akter", "gender": "female"},
    {"first_name": "Shahidul", "last_name": "Islam", "gender": "male"},
    {"first_name": "Parvin", "last_name": "Khatun", "gender": "female"},
    {"first_name": "Mizanur", "last_name": "Rahman", "gender": "male"},
    {"first_name": "Shamima", "last_name": "Sultana", "gender": "female"},
    {"first_name": "Jahangir", "last_name": "Alam", "gender": "male"},
    {"first_name": "Rokeya", "last_name": "Parvin", "gender": "female"},
    {"first_name": "Abdul", "last_name": "Karim", "gender": "male"},
    {"first_name": "Saleha", "last_name": "Begum", "gender": "female"},
    {"first_name": "Nurul", "last_name": "Huda", "gender": "male"},
    {"first_name": "Jahanara", "last_name": "Imam", "gender": "female"},
    {"first_name": "Moshiur", "last_name": "Rahman", "gender": "male"},
    {"first_name": "Tahmina", "last_name": "Akter", "gender": "female"},
    {"first_name": "Shahjahan", "last_name": "Mia", "gender": "male"},
    {"first_name": "Rashida", "last_name": "Khatun", "gender": "female"},
    {"first_name": "Delwar", "last_name": "Hossain", "gender": "male"},
    {"first_name": "Shahnaz", "last_name": "Begum", "gender": "female"},
    {"first_name": "Anwar", "last_name": "Hossain", "gender": "male"},
    {"first_name": "Laily", "last_name": "Akter", "gender": "female"},
    {"first_name": "Tariqul", "last_name": "Islam", "gender": "male"},
    {"first_name": "Shamim", "last_name": "Ara", "gender": "female"},
    {"first_name": "Golam", "last_name": "Mostafa", "gender": "male"},
    {"first_name": "Rahima", "last_name": "Khatun", "gender": "female"},
    {"first_name": "Mofiz", "last_name": "Uddin", "gender": "male"},
    {"first_name": "Shahida", "last_name": "Begum", "gender": "female"},
    {"first_name": "Abul", "last_name": "Kashem", "gender": "male"},
    {"first_name": "Nargis", "last_name": "Akter", "gender": "female"},
]


class IdentitySeeder(BaseSeeder):
    """Seed identity data: roles, permissions, users."""

    async def seed(self) -> dict[str, int]:
        # Create permissions
        perm_records = await self.bulk_insert(Permission, PERMISSIONS)
        self.add_stat("permissions", len(perm_records))

        # Create roles
        role_records = []
        for r in ROLES:
            role = Role(name=r["name"], description=r["description"], role_type=r["role_type"], is_system_role=r["is_system"])
            self.session.add(role)
            await self.session.flush()
            role_records.append(role)
        self.add_stat("roles", len(role_records))

        # Assign permissions to roles
        role_perm_count = 0
        for role in role_records:
            perm_names = ROLE_PERMISSIONS.get(role.name, [])
            for perm in perm_records:
                if perm["name"] in perm_names:
                    rp = RolePermission(role_id=role.id, permission_id=perm["id"])
                    self.session.add(rp)
                    role_perm_count += 1
        await self.session.flush()
        self.add_stat("role_permissions", role_perm_count)

        # Create admin users
        admin_records = []
        for au in ADMIN_USERS:
            role = next(r for r in role_records if r.name == au["role"])
            user = User(
                email=au["email"],
                password_hash=DEFAULT_PASSWORD,
                first_name=au["first_name"],
                last_name=au["last_name"],
                username=au["email"].split("@")[0],
                status=au["status"],
                is_verified=True,
                role_id=role.id,
            )
            self.session.add(user)
            await self.session.flush()
            admin_records.append(user)
        self.add_stat("admin_users", len(admin_records))

        # Create demo customer accounts
        viewer_role = next(r for r in role_records if r.name == "viewer")
        customer_records = []
        for i, customer in enumerate(DEMO_CUSTOMERS):
            email = generate_email(customer["first_name"], customer["last_name"])
            username = f"{customer['first_name'].lower()}.{customer['last_name'].lower()}"
            phone = random_phone()
            user = User(
                email=email,
                password_hash=DEFAULT_PASSWORD,
                first_name=customer["first_name"],
                last_name=customer["last_name"],
                username=username,
                phone_number=phone,
                status=UserStatus.ACTIVE,
                is_verified=True,
                role_id=viewer_role.id,
            )
            self.session.add(user)
            await self.session.flush()
            customer_records.append(user)
        self.add_stat("demo_customers", len(customer_records))

        return self.get_stats()

    async def clear(self):
        await self.clear_table("users")
        await self.clear_table("role_permissions")
        await self.clear_table("roles")
        await self.clear_table("permissions")
