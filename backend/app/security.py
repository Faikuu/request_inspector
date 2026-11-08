"""Password hashing, viewer tokens and the per-inbox access dependency."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import get_db
from app.models import Inbox

VIEWER_SCOPE = "inbox:view"
JWT_ALGORITHM = "HS256"

_hasher = PasswordHasher()
# Checked against when an inbox id does not exist, so a miss costs the same Argon2 verify as a hit.
DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def new_ingest_key() -> str:
    return secrets.token_urlsafe(24)


def create_viewer_token(settings: Settings, inbox_id: str) -> tuple[str, int]:
    """Return (token, expires_in_seconds). The token only grants read access to one inbox."""
    now = datetime.now(UTC)
    lifetime = timedelta(minutes=settings.token_ttl_minutes)
    claims = {"sub": inbox_id, "scope": VIEWER_SCOPE, "iat": now, "exp": now + lifetime}
    token = jwt.encode(claims, settings.secret_key, algorithm=JWT_ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_viewer_token(settings: Settings, token: str) -> dict[str, Any]:
    claims = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub", "scope"]},
    )
    if claims.get("scope") != VIEWER_SCOPE:
        raise jwt.InvalidTokenError("unexpected token scope")
    return claims


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Your session has ended. Enter the password to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_inbox(
    inbox_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Inbox:
    """Validate the bearer token for this inbox and load the inbox.

    401: missing, invalid or expired token. 403: token issued for another inbox. 404: inbox deleted.
    """
    if credentials is None:
        raise _unauthorized()
    try:
        claims = decode_viewer_token(request.app.state.settings, credentials.credentials)
    except jwt.PyJWTError:
        raise _unauthorized() from None
    if claims["sub"] != inbox_id:
        raise HTTPException(status_code=403, detail="This session is for a different inbox")
    inbox = await db.get(Inbox, inbox_id)
    if inbox is None:
        raise HTTPException(status_code=404, detail="Inbox not found")
    return inbox
