from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.core.db import mongo_client
from app.models.task import (
    DeleteResponse,
    NextIssueResponse,
    TaskCreate,
    TaskListResponse,
    TaskOut,
    TaskStatus,
    TaskResponse,
    TaskUpdate,
)
from app.repositories.task_repo import TaskRepository

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_repo() -> TaskRepository:
    return TaskRepository(mongo_client.db)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskResponse:
    task = await repo.create_task(payload, created_by=current_user["email"])
    return TaskResponse(data=TaskOut(**task))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    assigned_to: Optional[str] = Query(default=None),
    created_by: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    sort: str = Query(default="-created_at"),
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskListResponse:
    _ = current_user
    filters: dict[str, object] = {}
    if status_filter:
        filters["status"] = status_filter.value
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if created_by:
        filters["created_by"] = created_by
    if q:
        filters["title"] = {"$regex": q, "$options": "i"}

    sort_field = "created_at"
    sort_order = -1
    if sort.startswith("-"):
        sort_field = sort[1:] or "created_at"
        sort_order = -1
    elif sort:
        sort_field = sort
        sort_order = 1

    tasks = await repo.list_tasks(filters, sort=[(sort_field, sort_order)])
    return TaskListResponse(data=[TaskOut(**task) for task in tasks])


@router.get("/next-issue", response_model=NextIssueResponse)
async def next_issue_number(
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> NextIssueResponse:
    _ = current_user
    total = await repo.count_tasks()
    return NextIssueResponse(data={"next_issue": total + 1})


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskResponse:
    _ = current_user
    task = await repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse(data=TaskOut(**task))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> TaskResponse:
    _ = current_user
    task = await repo.update_task(task_id, payload)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse(data=TaskOut(**task))


@router.delete("/{task_id}", response_model=DeleteResponse)
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    repo: TaskRepository = Depends(get_repo),
) -> DeleteResponse:
    _ = current_user
    deleted = await repo.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return DeleteResponse(data={"deleted": True})
