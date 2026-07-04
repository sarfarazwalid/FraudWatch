"""
Password hashing and verification service.

Uses passlib with bcrypt for secure password handling.
"""

from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """
    Service for password hashing and verification.
    
    Uses bcrypt with automatic salt generation.
    """
    
    @staticmethod
    def hash(password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
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
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password hash needs to be rehashed.
        
        Args:
            hashed_password: Hashed password
            
        Returns:
            True if rehash is needed
        """
        return pwd_context.needs_update(hashed_password)
    
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