from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import TaskPriority, TaskStatus


class TagBase(BaseModel):
    name: str = Field(..., max_length=100)
    color: str | None = Field(None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    color: str | None = Field(None, max_length=7, pattern=r"^#[0-9a-fA-F]{6}$")


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProjectReadWithTasks(ProjectRead):
    tasks: list["TaskRead"] = []


class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: datetime | None = None
    project_id: int | None = None


class TaskCreate(TaskBase):
    tag_ids: list[int] = []


class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    project_id: int | None = None
    tag_ids: list[int] | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = []


class TaskReadWithProject(TaskRead):
    project: ProjectRead | None = None


ProjectReadWithTasks.model_rebuild()
