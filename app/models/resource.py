from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, EmailStr, Field


class ResourceCategory(str, Enum):
    deck = "deck"
    image = "image"
    sheet = "sheet"
    doc = "doc"
    archive = "archive"
    other = "other"


class ResourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: ResourceCategory = ResourceCategory.other
    tags: List[str] = Field(default_factory=list)
    url: Optional[AnyUrl] = None


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: Optional[ResourceCategory] = None
    tags: Optional[List[str]] = None
    url: Optional[AnyUrl] = None


class ResourceOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    title: str
    description: Optional[str] = None
    category: ResourceCategory = ResourceCategory.other
    tags: List[str] = Field(default_factory=list)
    url: Optional[AnyUrl] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_by: EmailStr
    created_at: datetime
    updated_at: datetime


class ResourceResponse(BaseModel):
    data: ResourceOut


class ResourceListResponse(BaseModel):
    data: List[ResourceOut]
    total: int
