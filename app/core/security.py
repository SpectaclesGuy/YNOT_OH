from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Request, Response
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    *,
    subject: str,
    email: str,
    name: Optional[str] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expires_minutes
    )
    to_encode: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "name": name,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def get_token_from_request(request: Request) -> Optional[str]:
    return request.cookies.get(settings.session_cookie_name)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        samesite=settings.session_cookie_samesite,
    )
