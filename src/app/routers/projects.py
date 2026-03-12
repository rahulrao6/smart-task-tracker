from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/projects", tags=["projects"])

# ---------------------------------------------------------------------------
# In-memory store (replace with DB layer when available)
# ---------------------------------------------------------------------------
_projects: dict[UUID, dict] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
VALID_STATUSES = {"active", "archived", "completed"}


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="active")
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    tags: list[str] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    status: str
    tags: list[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProjectResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_status(value: str) -> None:
    if value not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{value}'. Must be one of: {sorted(VALID_STATUSES)}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate) -> ProjectResponse:
    _validate_status(payload.status)

    project_id = uuid4()
    record = {
        "id": project_id,
        **payload.model_dump(),
    }
    _projects[project_id] = record
    return ProjectResponse(**record)


@router.get("/", response_model=PaginatedProjectResponse)
def list_projects(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    name_contains: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedProjectResponse:
    if status_filter is not None:
        _validate_status(status_filter)

    results = list(_projects.values())

    if status_filter is not None:
        results = [p for p in results if p["status"] == status_filter]
    if name_contains is not None:
        needle = name_contains.lower()
        results = [p for p in results if needle in p["name"].lower()]

    total = len(results)
    page = results[offset : offset + limit]

    return PaginatedProjectResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ProjectResponse(**p) for p in page],
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID) -> ProjectResponse:
    project = _projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse(**project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, payload: ProjectUpdate) -> ProjectResponse:
    project = _projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        _validate_status(updates["status"])

    project.update(updates)
    _projects[project_id] = project
    return ProjectResponse(**project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID) -> None:
    if project_id not in _projects:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    del _projects[project_id]
