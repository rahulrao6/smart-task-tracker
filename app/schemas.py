from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models import Priority, Status


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    status: Status = Field(Status.todo, description="Current task status")
    priority: Priority = Field(Priority.medium, description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date (ISO 8601)")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int


class PrioritizedTaskResponse(TaskResponse):
    priority_score: int = Field(..., description="Computed priority score (higher = more urgent)")


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
