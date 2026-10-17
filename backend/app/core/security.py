from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings
from app.core.exceptions import AppException

# In-memory blacklist for revoked tokens during runtime (can also be checked in MongoDB)
_REVOKED_TOKENS: Set[str] = set()

def hash_password(password: str) -> str:
    # Bcrypt maximum input length is 72 bytes
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(
    subject: str,
    role: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    if token in _REVOKED_TOKENS:
        raise AppException(
            code="TOKEN_REVOKED",
            message="This authentication token has been logged out or revoked.",
            status_code=401,
        )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Could not validate credentials or token has expired.",
            status_code=401,
        )

def revoke_token(token: str) -> None:
    _REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    return token in _REVOKED_TOKENS
