from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AuthUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    email: EmailStr
    name: str | None = None
    avatar: str | None = None
    provider: str
    provider_id: str
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None


class AuthUserPublic(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    name: str | None = None
    avatar: str | None = None
