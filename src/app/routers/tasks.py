from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.app.models import Task, TaskCreate, TaskUpdate, TaskStatus
from src.app.store import get_store

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[Task])
def list_tasks():
    return list(get_store().values())


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    task = Task(**payload.model_dump())
    get_store()[task.id] = task
    return task


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: UUID):
    task = get_store().get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: UUID, payload: TaskUpdate):
    store = get_store()
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update={**updates, "updated_at": datetime.utcnow()})

    if updates.get("status") == TaskStatus.done and task.status != TaskStatus.done:
        updated = updated.model_copy(update={"completed_at": datetime.utcnow()})

    store[task_id] = updated
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    store = get_store()
    if task_id not in store:
        raise HTTPException(status_code=404, detail="Task not found")
    del store[task_id]
