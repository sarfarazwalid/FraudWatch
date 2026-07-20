"""
Authentication service.

Orchestrates authentication flows including registration, login, token refresh, and logout.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.models.identity.user import User
from app.models.enums import UserStatus
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.services.password import PasswordService
from app.services.jwt import JWTService
from app.services.refresh_token import RefreshTokenService
from app.services.session import SessionService
from app.schemas.auth import TokenResponse, UserResponse


class AuthenticationService:
    """
    Service for authentication operations.

    Orchestrates user registration, login, logout, and token management.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        refresh_token_service: RefreshTokenService,
        session_service: SessionService
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.refresh_token_service = refresh_token_service
        self.session_service = session_service

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        username: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> tuple[User, str]:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password
            first_name: User first name
            last_name: User last name
            username: Optional username
            phone_number: Optional phone number

        Returns:
            Tuple of (created_user, verification_message)

        Raises:
            ValueError: If email already exists
        """
        print("=" * 50)
        print("ENTRY register()")
        print("=" * 50)

        # Check if email already exists
        print("STEP: existing user lookup")
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Create user
        user_status = UserStatus.PENDING_VERIFICATION.value if False else UserStatus.ACTIVE  # Simplified for now

        print("STEP: calling _create_user()")
        user = await self._create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number,
            status=user_status
        )

        verification_message = "Registration successful"
        print("STEP: returning success")
        print("=" * 50)

        return user, verification_message

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TokenResponse]:
        """
        Authenticate user and generate tokens.

        Args:
            email: User email
            password: Plain text password
            ip_address: Optional IP address
            user_agent: Optional user agent

        Returns:
            TokenResponse if authentication successful, None otherwise
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        # Check if account is locked
        if user.status == "locked":
            return None

        # Verify password
        if not PasswordService.verify(password, user.password_hash):
            await self.user_repo.increment_failed_login(str(user.id))
            return None

        # Reset failed login attempts
        await self.user_repo.reset_failed_login(str(user.id))

        # Update last login
        await self.user_repo.update_last_login(str(user.id))

        # Generate tokens
        access_token = JWTService.create_access_token(
            user_id=str(user.id),
            role=user.role.name if user.role else "viewer"
        )

        # Create refresh token
        refresh_token_string, refresh_token = await self.refresh_token_service.create_token(
            user_id=str(user.id),
            device_info=user_agent,
            ip_address=ip_address
        )

        # Create session
        session_token = str(uuid.uuid4())
        await self.session_service.create_session(
            user_id=str(user.id),
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_in=timedelta(hours=24)
        )

        # Build response
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_string,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                phone_number=user.phone_number,
                status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                is_verified=user.is_verified,
                last_login=user.last_login,
                created_at=user.created_at,
                role_name=user.role.name if user.role else None,
            )
        )

    async def refresh_access_token(self, refresh_token_string: str) -> Optional[TokenResponse]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token_string: Refresh token string

        Returns:
            TokenResponse if successful, None otherwise
        """
        # Validate refresh token
        refresh_token = await self.refresh_token_service.validate_token(refresh_token_string)
        if not refresh_token:
            return None

        # Get user
        user = await self.user_repo.get(str(refresh_token.user_id))
        if not user:
            return None

        # Rotate refresh token
        new_refresh_token = await self.refresh_token_service.rotate_token(refresh_token)
        if not new_refresh_token:
            return None

        # Generate new access token
        access_token = JWTService.create_access_token(
            user_id=str(user.id),
            role=user.role.name if user.role else "viewer"
        )

        new_refresh_token_string, new_refresh_token_model = new_refresh_token

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token_string,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                phone_number=user.phone_number,
                status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                is_verified=user.is_verified,
                last_login=user.last_login,
                created_at=user.created_at,
                role_name=user.role.name if user.role else None,
            )
        )

    async def logout(self, user_id: str) -> None:
        """
        Logout user by revoking all tokens and sessions.

        Args:
            user_id: User ID
        """
        await self.refresh_token_service.revoke_all_user_tokens(user_id)
        await self.session_service.revoke_all_user_sessions(user_id)

    async def _create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        status: str = UserStatus.PENDING_VERIFICATION.value
    ) -> User:
        """
        Internal method to create a user.

        Args:
            email: User email
            password: Plain text password
            first_name: User first name
            last_name: User last name
            username: Optional username
            phone_number: Optional phone number
            status: User status

        Returns:
            Created user
        """
        print("  STEP: password hashed")
        # Hash password
        password_hash = PasswordService.hash(password)

        print("  STEP: role lookup")
        # Get viewer role as default
        role = await self.role_repo.get_by_name("viewer")
        role_id = str(role.id) if role else None
        print(f"  ROLE FOUND: {role.name if role else 'None'}")

        # Create user
        from app.repositories.user import UserRepository
        print("  STEP: User object created")
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number,
        )

        print("  STEP: session.add()")
        self.user_repo.session.add(user)

        print("  STEP: session.flush()")
        await self.user_repo.session.flush()

        print("  STEP: session.refresh()")
        await self.user_repo.session.refresh(user)

        # Assign role
        print("  STEP: role assignment")
        if role_id:
            from app.models.identity.role import Role
            role = await self.role_repo.get(role_id)
            if role:
                user.role = role
                print(f"  ROLE ASSIGNED: {role.name}")

        print("  STEP: returning user")
        return user
