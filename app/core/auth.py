from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError

from app.core.db import mongo_client
from app.core.security import decode_token, get_token_from_request
from app.repositories.user_repo import UserRepository


async def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    repo = UserRepository(mongo_client.db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
