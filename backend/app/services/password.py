"""
Password hashing and verification service.

Uses bcrypt directly for secure password handling.
"""

import bcrypt
import logging

logger = logging.getLogger(__name__)


class PasswordService:
    @staticmethod
    def hash(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        # bcrypt has a 72-byte limit, truncate if necessary
        password = password[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        # bcrypt has a 72-byte limit, truncate if necessary
        plain_password = plain_password[:72]
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password hash needs to be rehashed.

        Args:
            hashed_password: Hashed password

        Returns:
            True if rehash is needed
        """
        # For simplicity, we'll say no rehash is needed
        # In production, you might want to check the work factor
        return False

    @staticmethod
    def validate_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.

        Args:
            password: Plain text password

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if len(password) > 128:
            return False, "Password must not exceed 128 characters"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not has_upper:
            return False, "Password must contain at least one uppercase letter"

        if not has_lower:
            return False, "Password must contain at least one lowercase letter"

        if not has_digit:
            return False, "Password must contain at least one digit"

        if not has_special:
            return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

        return True, "Password is strong"
