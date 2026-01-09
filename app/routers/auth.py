from __future__ import annotations

import secrets
from typing import Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.db import mongo_client
from app.core.security import (
    clear_session_cookie,
    create_access_token,
    set_session_cookie,
)
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

OAUTH_COOKIE_STATE = "oauth_state"
OAUTH_COOKIE_NEXT = "oauth_next"


def get_oauth_client(redirect_uri: Optional[str] = None) -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret,
        scope="openid email profile",
        redirect_uri=redirect_uri or settings.oauth_redirect_uri,
    )


def display_name_from_email(email: str) -> str:
    local = email.split("@", 1)[0].replace(".", " ").replace("_", " ")
    return " ".join(part.capitalize() for part in local.split()) if local else email


@router.get("/login")
async def login(next: str = "/") -> RedirectResponse:
    if not settings.oauth_client_id or not settings.oauth_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth is not configured. Set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET.",
        )

    state = secrets.token_urlsafe(32)
    client = get_oauth_client()
    authorization_url, _ = client.create_authorization_url(
        GOOGLE_AUTH_URL,
        state=state,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    response = RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(OAUTH_COOKIE_STATE, state, max_age=600, httponly=True, samesite="lax")
    response.set_cookie(OAUTH_COOKIE_NEXT, next or "/", max_age=600, httponly=True, samesite="lax")
    return response


@router.get("/callback")
async def callback(request: Request, code: str | None = None, state: str | None = None):
    expected_state = request.cookies.get(OAUTH_COOKIE_STATE)
    next_url = request.cookies.get(OAUTH_COOKIE_NEXT, "/") or "/"

    if not code or not state or state != expected_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    client = get_oauth_client()
    try:
        token = await client.fetch_token(
            GOOGLE_TOKEN_URL,
            code=code,
        )
        # client stores token internally; just call get
        userinfo_resp = await client.get(GOOGLE_USERINFO_URL)
        profile = userinfo_resp.json()
    finally:
        await client.aclose()

    email = profile.get("email")
    provider_id = profile.get("sub")
    name = profile.get("name") or (display_name_from_email(email) if email else None)
    avatar = profile.get("picture")

    if not email or not provider_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile from provider")

    if not email.lower().endswith("@thapar.edu"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only thapar.edu email accounts are allowed.",
        )

    repo = UserRepository(mongo_client.db)
    user = await repo.upsert_oauth_user(
        email=email,
        name=name,
        provider=settings.oauth_provider,
        provider_id=provider_id,
        avatar=avatar,
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save user")

    session_token = create_access_token(subject=user["_id"], email=email, name=name)
    response = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
    set_session_cookie(response, session_token)
    response.delete_cookie(OAUTH_COOKIE_STATE, path="/", samesite="lax")
    response.delete_cookie(OAUTH_COOKIE_NEXT, path="/", samesite="lax")
    return response


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "data": {
            "_id": current_user["_id"],
            "email": current_user["email"],
            "name": current_user.get("name"),
            "avatar": current_user.get("avatar"),
        }
    }


@router.post("/logout")
async def logout() -> JSONResponse:
    response = JSONResponse({"ok": True})
    clear_session_cookie(response)
    response.delete_cookie(OAUTH_COOKIE_STATE, path="/", samesite="lax")
    response.delete_cookie(OAUTH_COOKIE_NEXT, path="/", samesite="lax")
    return response
