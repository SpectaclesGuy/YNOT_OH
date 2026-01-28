from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.auth import get_current_user
from app.core.config import settings
from app.repositories.resource_repo import ResourceRepository
from app.core.db import mongo_client
from app.models.resource import (
    ResourceCategory,
    ResourceCreate,
    ResourceListResponse,
    ResourceOut,
    ResourceResponse,
    ResourceUpdate,
)
from app.models.task import DeleteResponse

router = APIRouter(prefix="/api/resources", tags=["resources"])


def get_repo() -> ResourceRepository:
    return ResourceRepository(mongo_client.db)


def parse_tags(raw: str) -> list[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def safe_join_path(upload_dir: Path, filename: str) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / filename


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    title: str = Form(...),
    description: Optional[str] = Form(default=None),
    category: ResourceCategory = Form(default=ResourceCategory.other),
    tags: str = Form(default=""),
    url: Optional[str] = Form(default=None),
    file: UploadFile | None = File(default=None),
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> ResourceResponse:
    email = current_user.get("email", "")
    if not email.lower().endswith("@thapar.edu"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only thapar.edu email accounts can upload resources.",
        )

    tag_list = parse_tags(tags)
    resource_data = ResourceCreate(
        title=title.strip(),
        description=description.strip() if description else None,
        category=category,
        tags=tag_list,
        url=url if url else None,
    )

    if not file and not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add a file or an external URL.",
        )

    file_info = None
    if file:
        upload_dir = Path(settings.resource_upload_dir)
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        dest_path = safe_join_path(upload_dir, unique_name)
        contents = await file.read()
        with dest_path.open("wb") as f:
            f.write(contents)
        file_info = {
            "file_path": str(dest_path.resolve()),
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(contents),
        }

    resource = await repo.create(resource_data, uploaded_by=current_user["email"], file_info=file_info)
    if not resource:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create resource")
    return ResourceResponse(data=ResourceOut(**resource))


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    category: Optional[ResourceCategory] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    sort: str = Query(default="-created_at"),
    limit: int = Query(default=10, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> ResourceListResponse:
    _ = current_user
    filters: dict[str, object] = {}
    if category:
        filters["category"] = category.value
    if tag:
        filters["tags"] = tag
    if q:
        filters["q"] = q

    sort_field = "created_at"
    sort_order = -1
    if sort.startswith("-"):
        sort_field = sort[1:] or "created_at"
        sort_order = -1
    elif sort:
        sort_field = sort
        sort_order = 1

    total = await repo.count(filters)
    items = await repo.list(filters, limit=limit, skip=skip, sort=[(sort_field, sort_order)])
    return ResourceListResponse(data=[ResourceOut(**item) for item in items], total=total)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> ResourceResponse:
    _ = current_user
    resource = await repo.get_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ResourceResponse(data=ResourceOut(**resource))


@router.get("/{resource_id}/download")
async def download_resource(
    resource_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> FileResponse:
    _ = current_user
    resource = await repo.get_by_id(resource_id)
    if not resource or not resource.get("file_path"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    path = Path(resource["file_path"])
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    filename = resource.get("original_filename") or path.name
    media_type = resource.get("content_type") or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    payload: ResourceUpdate,
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> ResourceResponse:
    _ = current_user
    updated = await repo.update(resource_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ResourceResponse(data=ResourceOut(**updated))


@router.delete("/{resource_id}", response_model=DeleteResponse)
async def delete_resource(
    resource_id: str,
    current_user: dict = Depends(get_current_user),
    repo: ResourceRepository = Depends(get_repo),
) -> DeleteResponse:
    _ = current_user
    deleted = await repo.delete(resource_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    file_path = deleted.get("file_path")
    if file_path and Path(file_path).exists():
        try:
            os.remove(file_path)
        except OSError:
            pass
    return DeleteResponse(data={"deleted": True})
