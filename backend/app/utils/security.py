"""
Security utilities for password hashing and JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
import bcrypt

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _encode_password(password: str) -> bytes:
    """Encode password to bytes, truncating to 72 bytes for bcrypt."""
    # bcrypt has a 72-byte limit on passwords
    return password.encode('utf-8')[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        plain_bytes = _encode_password(plain_password)
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a password hash using bcrypt."""
    password_bytes = _encode_password(password)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None, secret_key: str = "your-secret-key-change-in-production") -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user_id)
        expires_delta: Optional expiration time delta
        secret_key: Secret key for signing

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, int], secret_key: str = "your-secret-key-change-in-production") -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: The subject of the token (usually user_id)
        secret_key: Secret key for signing

    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str, secret_key: str = "your-secret-key-change-in-production") -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string
        secret_key: Secret key for verification

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str, secret_key: str = "your-secret-key-change-in-production") -> Optional[str]:
    """
    Verify a refresh token and return the user_id if valid.

    Args:
        token: The refresh token string
        secret_key: Secret key for verification

    Returns:
        User ID string if valid, None otherwise
    """
    payload = decode_token(token, secret_key)
    if payload is None:
        return None

    # Check token type
    if payload.get("type") != "refresh":
        return None

    return payload.get("sub")
