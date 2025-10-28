from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings

# Use pbkdf2_sha256 to avoid environment issues with bcrypt
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_sso_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> tuple[str, str, datetime]:
    expire = datetime.now(timezone.utc) + (expires_delta or settings.JWT_EXPIRES_DELTA)
    jti = uuid.uuid4().hex
    to_encode = {
        "iss": "sso-provider",
        "sub": str(user_id),
        "email": email,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, jti, expire


def verify_sso_token(token: str) -> tuple[bool, Optional[dict], Optional[str]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return True, payload, None
    except JWTError as e:
        return False, None, str(e)
