"""
Password hashing and verification utilities.

Uses Passlib with bcrypt for secure password handling.
"""

from passlib.context import CryptContext
from app.config.settings import settings

# Password hashing context
pwd_context = CryptContext(
    schemes=[settings.password_algorithm],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be rehashed."""
    return pwd_context.needs_update(hashed_password)