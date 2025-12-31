from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Milestone(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: Optional[date] = None
    done: bool = False


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    assigned_to: EmailStr
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    milestones: List[Milestone] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    assigned_to: Optional[EmailStr] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    milestones: Optional[List[Milestone]] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    title: str
    description: Optional[str]
    assigned_to: EmailStr
    created_by: EmailStr
    status: TaskStatus
    priority: TaskPriority
    milestones: List[Milestone]
    created_at: datetime
    updated_at: datetime



class TaskResponse(BaseModel):
    data: TaskOut


class TaskListResponse(BaseModel):
    data: List[TaskOut]


class DeleteResponse(BaseModel):
    data: dict


class NextIssueResponse(BaseModel):
    data: dict
