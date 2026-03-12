from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task, Tag, TaskStatus, Priority
from app.schemas import TaskCreate, TaskRead, TaskUpdate, PaginatedTasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_tags(db: AsyncSession, tag_ids: List[int]) -> List[Tag]:
    if not tag_ids:
        return []
    result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
    tags = result.scalars().all()
    if len(tags) != len(tag_ids):
        missing = set(tag_ids) - {t.id for t in tags}
        raise HTTPException(status_code=404, detail=f"Tags not found: {sorted(missing)}")
    return list(tags)


@router.get("", response_model=PaginatedTasks)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[Priority] = None,
    project_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Task).options(selectinload(Task.tags), selectinload(Task.project))

    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if project_id is not None:
        query = query.where(Task.project_id == project_id)
    if tag_id is not None:
        query = query.where(Task.tags.any(Tag.id == tag_id))
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return PaginatedTasks(total=total, page=page, page_size=page_size, items=list(items))


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude={"tag_ids"})
    tags = await _get_tags(db, payload.tag_ids)
    task = Task(**data)
    task.tags = tags
    db.add(task)
    await db.commit()
    await db.refresh(task, ["tags", "project"])
    return task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.tags), selectinload(Task.project))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.tags), selectinload(Task.project))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)

    if "status" in data and data["status"] == TaskStatus.done and task.status != TaskStatus.done:
        data["completed_at"] = datetime.utcnow()
    elif "status" in data and data["status"] != TaskStatus.done:
        data["completed_at"] = None

    for key, value in data.items():
        setattr(task, key, value)

    if tag_ids is not None:
        task.tags = await _get_tags(db, tag_ids)

    await db.commit()
    await db.refresh(task, ["tags", "project"])
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
