# app/core/security.py
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import Settings

settings = Settings()

def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash using bcrypt.

    Args:
        plain_password: Password to verify
        hashed_password: Hash to verify against

    Returns:
        True if password matches hash
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta  # Updated line
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # Updated line
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token.

    Args:
        token: Token to verify

    Returns:
        Decoded token data
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])