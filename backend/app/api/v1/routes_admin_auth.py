"""Login/logout/session-status for the single fixed admin account."""

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from app.core.admin_auth import (
    ADMIN_USERNAME,
    create_session,
    credentials_are_valid,
    invalidate_session,
    session_is_valid,
    set_session_cookie,
)
from app.core.admin_auth import clear_session_cookie
from app.schemas.molecule_admin import AdminLoginRequest, AdminSessionStatus

router = APIRouter()


@router.post("/admin/login", response_model=AdminSessionStatus)
def post_admin_login(payload: AdminLoginRequest, request: Request, response: Response) -> AdminSessionStatus:
    if not credentials_are_valid(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    token = create_session()
    set_session_cookie(response, request, token)
    return AdminSessionStatus(authenticated=True, username=ADMIN_USERNAME)


@router.post("/admin/logout", response_model=AdminSessionStatus)
def post_admin_logout(
    request: Request,
    response: Response,
    molecule_admin_session: str | None = Cookie(default=None),
) -> AdminSessionStatus:
    invalidate_session(molecule_admin_session)
    clear_session_cookie(response, request)
    return AdminSessionStatus(authenticated=False)


@router.get("/admin/session", response_model=AdminSessionStatus)
def get_admin_session(molecule_admin_session: str | None = Cookie(default=None)) -> AdminSessionStatus:
    if session_is_valid(molecule_admin_session):
        return AdminSessionStatus(authenticated=True, username=ADMIN_USERNAME)
    return AdminSessionStatus(authenticated=False)
