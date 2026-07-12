"""
Trace the complete POST /api/v1/auth/register execution path.
Captures the exact failing line with full traceback.
"""

import sys
import os
import traceback
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("TRACING POST /api/v1/auth/register")
print("=" * 80)

# Step 1: Import the API router
print("\n[STEP 1] Importing API router...")
try:
    from app.api.v1.auth import router
    print(f"  Router routes: {[r.path for r in router.routes]}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 2: Import schema
print("\n[STEP 2] Importing RegisterRequest schema...")
try:
    from app.schemas.auth import RegisterRequest
    print(f"  Schema fields: {list(RegisterRequest.model_fields.keys())}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 3: Import AuthenticationService
print("\n[STEP 3] Importing AuthenticationService...")
try:
    from app.services.auth import AuthenticationService
    print(f"  Service methods: {[m for m in dir(AuthenticationService) if not m.startswith('_')]}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 4: Import repositories
print("\n[STEP 4] Importing repositories...")
try:
    from app.repositories.user import UserRepository
    from app.repositories.role import RoleRepository
    from app.repositories.refresh_token import RefreshTokenRepository
    from app.repositories.session import SessionRepository
    print("  All repositories imported successfully")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 5: Import services
print("\n[STEP 5] Importing services...")
try:
    from app.services.password import PasswordService
    from app.services.jwt import JWTService
    from app.services.refresh_token import RefreshTokenService
    from app.services.session import SessionService
    print("  All services imported successfully")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 6: Import models
print("\n[STEP 6] Importing models...")
try:
    from app.models.identity.user import User
    from app.models.identity.role import Role
    from app.models.enums import UserStatus, RoleType
    print(f"  User model: {User.__tablename__}")
    print(f"  Role model: {Role.__tablename__}")
    print(f"  UserStatus values: {[e.value for e in UserStatus]}")
    print(f"  RoleType values: {[e.value for e in RoleType]}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test PasswordService
print("\n[STEP 7] Testing PasswordService...")
try:
    hashed = PasswordService.hash("TestPassword123!")
    print(f"  Hash: {hashed[:20]}...")
    verified = PasswordService.verify("TestPassword123!", hashed)
    print(f"  Verify: {verified}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 8: Test JWTService
print("\n[STEP 8] Testing JWTService...")
try:
    token = JWTService.create_access_token(user_id="test-id", role="viewer")
    print(f"  Token: {token[:30]}...")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 9: Test creating a User ORM object
print("\n[STEP 9] Testing User ORM object creation...")
try:
    test_user = User(
        email="test@example.com",
        password_hash=hashed,
        first_name="Test",
        last_name="User",
        username="testuser",
        phone_number="+1234567890",
    )
    print(f"  User created: {test_user}")
    print(f"  User.email: {test_user.email}")
    print(f"  User.status: {test_user.status}")
    print(f"  User.status type: {type(test_user.status)}")
    print(f"  User.is_verified: {test_user.is_verified}")
    print(f"  User.failed_login_attempts: {test_user.failed_login_attempts}")
    print(f"  User.timezone: {test_user.timezone}")
    print(f"  User.language: {test_user.language}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 10: Test Role ORM object
print("\n[STEP 10] Testing Role ORM object...")
try:
    test_role = Role(
        name="viewer",
        description="Viewer role",
        role_type=RoleType.VIEWER,
        is_system=True,
        is_active=True,
    )
    print(f"  Role created: {test_role}")
    print(f"  Role.role_type: {test_role.role_type}")
    print(f"  Role.role_type type: {type(test_role.role_type)}")
    print(f"  Role.role_type value: {test_role.role_type.value}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 11: Test role assignment
print("\n[STEP 11] Testing role assignment on User...")
try:
    test_user.role = test_role
    print(f"  Role assigned: {test_user.role.name}")
    print(f"  role_id: {test_user.role_id}")
except Exception as e:
    print(f"  FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 12: Test the full _create_user flow with a mock
print("\n[STEP 12] Testing _create_user logic...")
try:
    from unittest.mock import AsyncMock, MagicMock, patch

    # Create mock session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Create mock repositories
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

    # Create mock services
    mock_refresh_token_service = MagicMock()
    mock_session_service = MagicMock()

    # Create AuthenticationService
    auth_service = AuthenticationService(
        user_repo=mock_user_repo,
        role_repo=mock_role_repo,
        refresh_token_service=mock_refresh_token_service,
        session_service=mock_session_service
    )

    print("  AuthenticationService created successfully")

    # Test register
    print("\n  Calling auth_service.register()...")
    try:
        user, message = await auth_service.register(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            username="testuser",
            phone_number="+1234567890"
        )
        print(f"  Register returned: user={user.email}, message={message}")
        print(f"  User ID: {user.id}")
        print(f"  User role: {user.role.name if user.role else 'None'}")
    except Exception as e:
        print(f"  REGISTER FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Test login
    print("\n  Calling auth_service.login()...")
    try:
        mock_user_repo.get_by_email = AsyncMock(return_value=user)
        mock_refresh_token_service.create_token = AsyncMock(return_value=("refresh-token-string", MagicMock()))
        mock_session_service.create_session = AsyncMock()

        token_response = await auth_service.login(
            email="test@example.com",
            password="TestPassword123!",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        print(f"  Login returned: token_type={token_response.token_type}")
        print(f"  Access token: {token_response.access_token[:30]}...")
        print(f"  User email: {token_response.user.email}")
    except Exception as e:
        print(f"  LOGIN FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)

except Exception as e:
    print(f"  STEP 12 FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL STEPS PASSED - Registration flow is valid")
print("=" * 80)
