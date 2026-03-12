from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models import Priority, TaskStatus


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ProjectReadWithTasks(ProjectRead):
    tasks: List["TaskRead"] = []


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: Priority = Priority.medium
    due_date: Optional[datetime] = None
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    tag_ids: List[int] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    project_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: List[TagRead] = []
    project: Optional[ProjectRead] = None


class PaginatedTasks(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TaskRead]


ProjectReadWithTasks.model_rebuild()
