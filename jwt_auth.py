"""JWT token creation and verification for LEWS."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import get_env
from .database import get_db

# ---------------------------------------------------------------------------
# CONFIG  (override via .env)
# ---------------------------------------------------------------------------

_SECRET_KEY = (
    get_env("JWT_SECRET_KEY")
    or "CHANGE-ME-uttarakhand-lews-jwt-secret-32-chars!"
)
_ALGORITHM = "HS256"
_EXPIRE_MINUTES = int(get_env("JWT_EXPIRE_MINUTES") or "10080")  # 7 days


# ---------------------------------------------------------------------------
# TOKEN CREATION
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """Create a signed HS256 JWT that encodes the user's primary key."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# TOKEN VERIFICATION DEPENDENCY
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    """
    FastAPI dependency — extract and validate the JWT from the
    Authorization: Bearer <token> header.

    Returns the authenticated user's integer ID.
    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_exception("Bearer token required")

    try:
        payload = jwt.decode(credentials.credentials, _SECRET_KEY, algorithms=[_ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise _credentials_exception()
        return int(user_id_str)
    except (JWTError, ValueError):
        raise _credentials_exception()


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Full dependency that returns the authenticated User ORM object.
    Raises HTTP 401 if token is invalid, HTTP 404 if user no longer exists.
    """
    from .models import User  # local import avoids circular dependency

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user
