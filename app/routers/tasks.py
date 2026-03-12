from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=schemas.TaskListResponse, summary="List all tasks")
def list_tasks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status: Optional[models.Status] = Query(None, description="Filter by status"),
    priority: Optional[models.Priority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    db: Session = Depends(get_db),
):
    tasks = crud.get_tasks(db, skip=skip, limit=limit, status=status, priority=priority, search=search)
    total = crud.count_tasks(db, status=status, priority=priority, search=search)
    return schemas.TaskListResponse(tasks=tasks, total=total, skip=skip, limit=limit)


@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED, summary="Create a task")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)


@router.get("/prioritized", response_model=List[schemas.PrioritizedTaskResponse], summary="Get AI-prioritized tasks")
def get_prioritized_tasks(
    limit: int = Query(10, ge=1, le=100, description="Number of top-priority tasks to return"),
    db: Session = Depends(get_db),
):
    results = crud.get_prioritized_tasks(db, limit=limit)
    output = []
    for item in results:
        task_dict = {
            **schemas.TaskResponse.model_validate(item["task"]).model_dump(),
            "priority_score": item["priority_score"],
        }
        output.append(schemas.PrioritizedTaskResponse(**task_dict))
    return output


@router.get("/{task_id}", response_model=schemas.TaskResponse, summary="Get a task by ID")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.patch("/{task_id}", response_model=schemas.TaskResponse, summary="Update a task")
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = crud.update_task(db, task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
