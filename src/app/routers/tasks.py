from datetime import date
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ---------------------------------------------------------------------------
# In-memory store (replace with DB layer when available)
# ---------------------------------------------------------------------------
_tasks: dict[UUID, dict] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TaskStatus(str):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


VALID_STATUSES = {"todo", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="todo")
    priority: str = Field(default="medium")
    project_id: UUID | None = None
    due_date: date | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(str_strip_whitespace=True)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    project_id: UUID | None = None
    due_date: date | None = None
    tags: list[str] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    priority: str
    project_id: UUID | None
    due_date: date | None
    tags: list[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedTaskResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_status(value: str) -> None:
    if value not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{value}'. Must be one of: {sorted(VALID_STATUSES)}",
        )


def _validate_priority(value: str) -> None:
    if value not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid priority '{value}'. Must be one of: {sorted(VALID_PRIORITIES)}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> TaskResponse:
    _validate_status(payload.status)
    _validate_priority(payload.priority)

    task_id = uuid4()
    record = {
        "id": task_id,
        **payload.model_dump(),
    }
    _tasks[task_id] = record
    return TaskResponse(**record)


@router.get("/", response_model=PaginatedTaskResponse)
def list_tasks(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    priority: str | None = None,
    project_id: UUID | None = None,
    due_date_from: date | None = None,
    due_date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedTaskResponse:
    if status_filter is not None:
        _validate_status(status_filter)
    if priority is not None:
        _validate_priority(priority)

    results = list(_tasks.values())

    if status_filter is not None:
        results = [t for t in results if t["status"] == status_filter]
    if priority is not None:
        results = [t for t in results if t["priority"] == priority]
    if project_id is not None:
        results = [t for t in results if t["project_id"] == project_id]
    if due_date_from is not None:
        results = [t for t in results if t["due_date"] is not None and t["due_date"] >= due_date_from]
    if due_date_to is not None:
        results = [t for t in results if t["due_date"] is not None and t["due_date"] <= due_date_to]

    total = len(results)
    page = results[offset : offset + limit]

    return PaginatedTaskResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[TaskResponse(**t) for t in page],
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID) -> TaskResponse:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse(**task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, payload: TaskUpdate) -> TaskResponse:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        _validate_status(updates["status"])
    if "priority" in updates:
        _validate_priority(updates["priority"])

    task.update(updates)
    _tasks[task_id] = task
    return TaskResponse(**task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID) -> None:
    if task_id not in _tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del _tasks[task_id]
