"""Single fixed-account admin authentication for the Molecule Data page.

This project deliberately does not need OAuth, multiple accounts, registration
or JWT infrastructure -- it has exactly one administrator. The credentials
below are intentionally fixed for this simple single-admin deployment; they
are never imported by frontend code and are never exposed through any API.

Sessions are an in-memory dict keyed by an opaque token from ``secrets``. A
backend restart clears every session, which is an acceptable trade-off for a
single-admin tool.
"""

from __future__ import annotations

import secrets
import time

from fastapi import Cookie, HTTPException, Request, Response, status

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

SESSION_COOKIE_NAME = "molecule_admin_session"
_SESSION_TTL_SECONDS = 12 * 60 * 60

# username -> {token: created_at}; a plain in-memory store is acceptable here since
# there is only ever one administrator and one process.
_sessions: dict[str, float] = {}


def credentials_are_valid(username: str, password: str) -> bool:
    return secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD)


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.monotonic()
    return token


def invalidate_session(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def session_is_valid(token: str | None) -> bool:
    if not token or token not in _sessions:
        return False
    if time.monotonic() - _sessions[token] > _SESSION_TTL_SECONDS:
        _sessions.pop(token, None)
        return False
    return True


def _cookie_is_secure(request: Request) -> bool:
    """True when the browser's own connection is HTTPS, direct or via a proxy.

    Behind the Cloudflare tunnel the browser talks HTTPS to the edge even though
    the hop to this backend is plain HTTP, so the forwarded-proto header (already
    set by nginx, see frontend/nginx.conf) is what actually reflects the browser's
    view. Falling back to the request's own scheme keeps local http:// dev working.
    """

    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    return forwarded_proto == "https" or request.url.scheme == "https"


def set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=_cookie_is_secure(request),
        path="/",
        max_age=_SESSION_TTL_SECONDS,
    )


def clear_session_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=_cookie_is_secure(request),
    )


def require_admin_session(
    molecule_admin_session: str | None = Cookie(default=None),
) -> str:
    """FastAPI dependency: 401s unless the request carries a valid session cookie."""

    if not session_is_valid(molecule_admin_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return ADMIN_USERNAME
