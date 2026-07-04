from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Input:
        password: Plain password string
    Output:
        bcrypt hash string
    """

    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""

    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, email: str) -> str:
    """Create a signed JWT access token.

    JWT payload schema:
        {
          "sub": "<user_id>" ,
          "email": "<user_email>",
          "iat": <issued_at>,
          "exp": <expires_at>
        }

    Input:
        user_id: User id as int
        email: User email
    Output:
        Signed JWT access token string
    """

    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": issued_at,
        "exp": expire,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT access token.

    Input:
        token: JWT access token string
    Output:
        {
          "user_id": int(payload["sub"]),
          "email": payload.get("email")
        }

    Raises:
        jose.JWTError (as JWTError) on invalid/expired token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        # Keep raising a clean error type; routers/dependencies can convert to HTTP.
        raise exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing 'sub' (user_id)")

    return {
        "user_id": int(sub),
        "email": payload.get("email"),
    }


