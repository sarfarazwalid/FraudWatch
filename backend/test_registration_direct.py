"""
Direct test of registration logic without starting the server.
Tests the exact code path that fails during registration.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import traceback
from unittest.mock import AsyncMock, MagicMock

async def test_registration():
    """Test the registration flow directly."""
    print("=" * 80)
    print("TESTING REGISTRATION FLOW (Direct)")
    print("=" * 80)

    # Import only what we need, avoiding the ml module
    print("\n[1] Importing models and services...")
    from app.models.identity.user import User
    from app.models.identity.role import Role
    from app.models.enums import UserStatus, RoleType
    from app.services.password import PasswordService
    from app.services.jwt import JWTService
    from app.repositories.user import UserRepository
    from app.repositories.role import RoleRepository
    from app.services.auth import AuthenticationService
    print("  ✓ All imports successful")

    # Test 1: Create a user with status as enum
    print("\n[2] Testing User creation...")
    try:
        hashed_password = PasswordService.hash("TestPass123!")
        user = User(
            email="test@example.com",
            password_hash=hashed_password,
            first_name="Test",
            last_name="User",
            status=UserStatus.ACTIVE,  # Use enum value
        )
        print(f"  ✓ User created: {user.email}")
        print(f"    Status: {user.status} (type: {type(user.status).__name__})")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        return False

    # Test 2: Create a role
    print("\n[3] Testing Role creation...")
    try:
        role = Role(
            name="viewer",
            description="Viewer role",
            role_type=RoleType.VIEWER,
            is_system=True,
            is_active=True,
        )
        print(f"  ✓ Role created: {role.name}")
        print(f"    Type: {role.role_type} (type: {type(role.role_type).__name__})")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        return False

    # Test 3: Test the _create_user method directly
    print("\n[4] Testing _create_user method...")
    try:
        # Create mocks
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

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

        mock_refresh_token_service = MagicMock()
        mock_refresh_token_service.create_token = AsyncMock(
            return_value=("refresh_token_string", MagicMock())
        )

        mock_session_service = MagicMock()
        mock_session_service.create_session = AsyncMock(return_value=MagicMock())

        # Create auth service
        auth_service = AuthenticationService(
            user_repo=mock_user_repo,
            role_repo=mock_role_repo,
            refresh_token_service=mock_refresh_token_service,
            session_service=mock_session_service,
        )

        # Call register
        print("  Calling auth_service.register()...")
        user, message = await auth_service.register(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
        )

        print(f"  ✓ Registration successful!")
        print(f"    User: {user.email}")
        print(f"    Message: {message}")
        print(f"    User ID: {user.id}")
        print(f"    User Status: {user.status}")

        # Verify the user was added to session
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

        return True

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_registration())
    print("\n" + "=" * 80)
    if success:
        print("✓ ALL TESTS PASSED - Registration flow works correctly")
    else:
        print("✗ TESTS FAILED - See errors above")
    print("=" * 80)
