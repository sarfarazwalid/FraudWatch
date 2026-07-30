"""
Demo user generation module.

This module creates demo users with appropriate roles and permissions
for the FraudWatch platform.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity.user import User
from app.models.identity.role import Role
from app.models.identity.permission import Permission
from app.models.identity.role_permission import RolePermission
from app.models.enums import RoleType
from app.services.password import PasswordService

from seed.demo.config import config
from seed.demo.helpers import random_timestamp

logger = logging.getLogger(__name__)


async def get_or_create_role(session: AsyncSession, role_name: str, description: str) -> Role:
    """Get existing role or create new one."""
    result = await session.execute(
        select(Role).where(Role.name == role_name)
    )
    role = result.scalar_one_or_none()

    if not role:
        # Map role names to RoleType enum values
        role_type_mapping = {
            "super_admin": RoleType.SUPER_ADMIN,
            "fraud_analyst": RoleType.FRAUD_ANALYST,
            "investigator": RoleType.ADMIN,
            "viewer": RoleType.VIEWER,
        }
        role_type = role_type_mapping.get(role_name, RoleType.VIEWER)

        role = Role(
            name=role_name,
            description=description,
            role_type=role_type,
            is_active=True,
        )
        session.add(role)
        await session.flush()
        logger.info(f"Created role: {role_name}")

    return role


async def create_permissions(session: AsyncSession) -> Dict[str, Permission]:
    """Create all required permissions using raw SQL to bypass enum issues."""
    permissions_data = [
        # Transaction permissions
        ("transactions", "read", "View transactions"),
        ("transactions", "create", "Create transactions"),
        ("transactions", "update", "Update transactions"),
        ("transactions", "delete", "Delete transactions"),
        # Alert permissions
        ("alerts", "read", "View alerts"),
        ("alerts", "create", "Create alerts"),
        ("alerts", "update", "Update alerts"),
        ("alerts", "delete", "Delete alerts"),
        # Case permissions
        ("cases", "read", "View cases"),
        ("cases", "create", "Create cases"),
        ("cases", "update", "Update cases"),
        ("cases", "delete", "Delete cases"),
        # ML permissions
        ("ml", "read", "View ML models"),
        ("ml", "execute", "Run ML predictions"),
        # Analytics permissions
        ("analytics", "read", "View analytics"),
        # User management
        ("users", "read", "View users"),
        ("users", "create", "Create users"),
        ("users", "update", "Update users"),
        ("users", "delete", "Delete users"),
        # Dashboard
        ("dashboard", "read", "View dashboard"),
    ]

    permissions = {}
    for resource, action, description in permissions_data:
        perm_key = f"{resource}:{action}"

        # Use raw SQL to insert to bypass SQLAlchemy enum handling.
        # ON CONFLICT makes this idempotent so re-running the seeder won't
        # fail on the uq_permissions_resource_action unique constraint.
        from sqlalchemy import text
        from uuid import uuid4

        stmt = text("""
            INSERT INTO permissions (id, name, resource, action, description, created_at, updated_at, version)
            VALUES (:id, :name, :resource, :action, :description, :created_at, :updated_at, :version)
            ON CONFLICT (resource, action) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                updated_at = EXCLUDED.updated_at
            RETURNING id
        """)

        result = await session.execute(stmt, {
            "id": uuid4(),
            "name": f"{resource}:{action}",
            "resource": resource,
            "action": action.lower(),
            "description": description,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "version": 1
        })

        permission_id = result.scalar_one()

        # Create Permission object for relationship mapping
        permission = Permission(
            id=permission_id,
            resource=resource,
            action=action.lower(),
            description=description,
        )

        permissions[perm_key] = permission
        logger.debug(f"Ensured permission exists: {perm_key}")

    return permissions


async def assign_permissions_to_role(
    session: AsyncSession,
    role: Role,
    permissions: List[str],
    all_permissions: Dict[str, Permission]
) -> None:
    """Assign permissions to a role."""
    for perm_key in permissions:
        if perm_key in all_permissions:
            permission = all_permissions[perm_key]

            # Check if already assigned
            result = await session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                session.add(role_perm)
                logger.debug(f"Assigned permission {perm_key} to role {role.name}")


async def create_demo_users(session: AsyncSession) -> List[User]:
    """Create demo users with roles."""
    logger.info("Creating demo users...")

    # Create permissions first
    all_permissions = await create_permissions(session)

    # Define roles and their permissions
    role_permissions_map = {
        "super_admin": [
            "transactions:read", "transactions:create", "transactions:update", "transactions:delete",
            "alerts:read", "alerts:create", "alerts:update", "alerts:delete",
            "cases:read", "cases:create", "cases:update", "cases:delete",
            "ml:read", "ml:execute",
            "analytics:read",
            "users:read", "users:create", "users:update", "users:delete",
            "dashboard:read",
        ],
        "fraud_analyst": [
            "transactions:read",
            "alerts:read", "alerts:update",
            "cases:read",
            "ml:read",
            "analytics:read",
            "dashboard:read",
        ],
        "investigator": [
            "transactions:read",
            "alerts:read",
            "cases:read", "cases:create", "cases:update",
            "ml:read",
            "analytics:read",
            "dashboard:read",
        ],
        "viewer": [
            "transactions:read",
            "alerts:read",
            "cases:read",
            "analytics:read",
            "dashboard:read",
        ],
    }

    # Create roles
    role_descriptions = {
        "super_admin": "Full system access with all permissions",
        "fraud_analyst": "Fraud analysis and monitoring",
        "investigator": "Case investigation and resolution",
        "viewer": "Read-only dashboard access",
    }

    roles = {}
    for role_name, description in role_descriptions.items():
        role = await get_or_create_role(session, role_name, description)
        roles[role_name] = role

        # Assign permissions to role
        if role_name in role_permissions_map:
            await assign_permissions_to_role(
                session, role, role_permissions_map[role_name], all_permissions
            )

    await session.flush()

    # Create users
    users = []
    for user_data in config.DEMO_USERS:
        role_name = user_data["role"]
        role = roles.get(role_name)

        if not role:
            logger.warning(f"Role {role_name} not found, skipping user {user_data['email']}")
            continue

        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"User already exists: {user_data['email']}")
            users.append(existing_user)
            continue

        # Create new user
        user = User(
            email=user_data["email"],
            username=user_data["email"].split("@")[0],
            password_hash=PasswordService.hash(user_data["password"]),
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role_id=role.id,
            status="active",
            is_verified=True,
            last_login=random_timestamp(start_days_ago=7, end_days_ago=0),
            timezone="Asia/Dhaka",
            language="en",
        )

        session.add(user)
        users.append(user)
        logger.info(f"Created user: {user_data['email']} (role: {role_name})")

    await session.flush()
    logger.info(f"Created {len(users)} demo users")

    return users


def get_demo_credentials() -> List[Dict[str, str]]:
    """Get demo user credentials for documentation."""
    return [
        {
            "email": user["email"],
            "password": user["password"],
            "role": user["role"],
            "description": user["description"],
        }
        for user in config.DEMO_USERS
    ]
