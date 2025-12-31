from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.db import mongo_client
from app.models.user import UserListResponse, UserOut
from app.repositories.task_repo import TaskRepository

router = APIRouter(prefix="/api/users", tags=["users"])


def get_current_user(x_user_email: Optional[str] = Header(default=None, alias="X-User-Email")) -> str:
    if not x_user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-Email")
    return x_user_email


def get_repo() -> TaskRepository:
    return TaskRepository(mongo_client.db)


def display_name_from_email(email: str) -> str:
    local = email.split("@", 1)[0].replace(".", " ").replace("_", " ")
    return " ".join(part.capitalize() for part in local.split()) if local else email


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: str = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> UserListResponse:
    _ = current_user
    emails = await repo.list_user_emails()
    users = [UserOut(email=email, display_name=display_name_from_email(email)) for email in emails]
    return UserListResponse(data=users)
