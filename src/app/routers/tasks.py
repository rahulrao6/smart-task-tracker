from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Tag, Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        project_id=payload.project_id,
    )
    if payload.tag_ids:
        result = await db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids)))
        task.tags = list(result.scalars().all())
    db.add(task)
    await db.flush()
    await db.refresh(task, ["tags", "project"])
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: TaskStatus | None = Query(default=None),
    priority: TaskPriority | None = Query(default=None),
    project_id: int | None = Query(default=None),
    due_date_from: datetime | None = Query(default=None),
    due_date_to: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    stmt = select(Task).options(selectinload(Task.tags), selectinload(Task.project))

    if status is not None:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if due_date_from is not None:
        stmt = stmt.where(Task.due_date >= due_date_from)
    if due_date_to is not None:
        stmt = stmt.where(Task.due_date <= due_date_to)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> Task:
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.tags), selectinload(Task.project))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> Task:
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.tags), selectinload(Task.project))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for field, value in update_data.items():
        setattr(task, field, value)

    if tag_ids is not None:
        tag_result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        task.tags = list(tag_result.scalars().all())

    await db.flush()
    await db.refresh(task, ["tags", "project"])
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
