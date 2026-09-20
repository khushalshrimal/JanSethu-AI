import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with a cryptographically secure 16-byte random salt."""
    salt = secrets.token_hex(16)
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${hash_bytes.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the PBKDF2 salted hash string."""
    try:
        if not hashed_password.startswith("pbkdf2:sha256:"):
            # Fallback check for plain SHA256 legacy dev hash
            return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password

        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False

        header, salt, expected_hash = parts
        _, _, iterations_str = header.split(":")
        iterations = int(iterations_str)

        computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), iterations).hex()
        return secrets.compare_digest(computed_hash, expected_hash)
    except Exception as e:
        print("[SECURITY ERROR] Password verification exception:", e)
        return False

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token for a subject (user_id / phone_number)."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates JWT token signature and expiration."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print("[JWT ERROR] Token decode failed:", e)
        return None
