"""
Test the exact registration flow to find the failing line.
"""
import sys
import os
import traceback
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def main():
    print("=" * 80)
    print("TESTING REGISTRATION FLOW")
    print("=" * 80)

    # Step 1: Import everything
    print("\n[STEP 1] Importing...")
    from app.models.identity.user import User
    from app.models.identity.role import Role
    from app.models.enums import UserStatus, RoleType
    from app.services.password import PasswordService
    from app.services.jwt import JWTService
    from app.repositories.user import UserRepository
    from app.repositories.role import RoleRepository
    from app.repositories.base import BaseRepository
    from app.models.base import Base
    from sqlalchemy import inspect as sa_inspect
    print("  All imports OK")

    # Step 2: Check User model columns vs DB expectations
    print("\n[STEP 2] Checking User model columns...")
    user_mapper = sa_inspect(User)
    for col in user_mapper.columns:
        print(f"  {col.name}: {col.type} nullable={col.nullable} default={col.default}")

    # Step 3: Check Role model columns
    print("\n[STEP 3] Checking Role model columns...")
    role_mapper = sa_inspect(Role)
    for col in role_mapper.columns:
        print(f"  {col.name}: {col.type} nullable={col.nullable}")

    # Step 4: Test creating User with status as string (like the code does)
    print("\n[STEP 4] Testing User creation with status as string...")
    try:
        hashed = PasswordService.hash("TestPass123!")
        user = User(
            email="test@example.com",
            password_hash=hashed,
            first_name="Test",
            last_name="User",
        )
        print(f"  User created: {user}")
        print(f"  User.status = {user.status!r} (type: {type(user.status).__name__})")
        print(f"  User.status.value = {user.status.value!r}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()

    # Step 5: Test creating Role with role_type as string
    print("\n[STEP 5] Testing Role creation with role_type as string...")
    try:
        role = Role(
            name="viewer",
            description="Viewer role",
            role_type=RoleType.VIEWER,
            is_system=True,
            is_active=True,
        )
        print(f"  Role created: {role}")
        print(f"  Role.role_type = {role.role_type!r} (type: {type(role.role_type).__name__})")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()

    # Step 6: Test the exact _create_user flow
    print("\n[STEP 6] Testing _create_user flow...")
    try:
        from unittest.mock import AsyncMock, MagicMock

        # Create mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create mock repos
        mock_user_repo = MagicMock(spec=UserRepository)
        mock_user_repo.session = mock_session
        mock_user_repo.get_by_email = AsyncMock(return_value=None)

        mock_role_repo = MagicMock(spec=RoleRepository)
        mock_role = Role(
            name="viewer",
            description="Viewer role",
            role_type=RoleType.VIEWER,
            is_system=True,
            is_active=True,
        )
        mock_role_repo.get_by_role_type = AsyncMock(return_value=mock_role)
        mock_role_repo.get = AsyncMock(return_value=mock_role)

        # Create auth service
        from app.services.auth import AuthenticationService
        auth_service = AuthenticationService(
            user_repo=mock_user_repo,
            role_repo=mock_role_repo,
            refresh_token_service=MagicMock(),
            session_service=MagicMock()
        )

        # Test register
        print("  Calling register()...")
        user, message = await auth_service.register(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )
        print(f"  SUCCESS: user={user.email}, message={message}")

    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        # Find the exact line
        import linecache
        tb = traceback.extract_tb(sys.exc_info()[2])
        for frame in tb:
            print(f"  File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}")
            print(f"    Code: {frame.line}")

if __name__ == "__main__":
    asyncio.run(main())
