from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas


def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.Status] = None,
    priority: Optional[models.Priority] = None,
    search: Optional[str] = None,
) -> List[models.Task]:
    query = db.query(models.Task)
    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if search:
        query = query.filter(
            models.Task.title.ilike(f"%{search}%")
            | models.Task.description.ilike(f"%{search}%")
        )
    return query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()


def count_tasks(
    db: Session,
    status: Optional[models.Status] = None,
    priority: Optional[models.Priority] = None,
    search: Optional[str] = None,
) -> int:
    query = db.query(models.Task)
    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if search:
        query = query.filter(
            models.Task.title.ilike(f"%{search}%")
            | models.Task.description.ilike(f"%{search}%")
        )
    return query.count()


def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True


PRIORITY_SCORE = {
    models.Priority.critical: 40,
    models.Priority.high: 30,
    models.Priority.medium: 20,
    models.Priority.low: 10,
}

STATUS_SCORE = {
    models.Status.in_progress: 20,
    models.Status.todo: 10,
    models.Status.done: 0,
    models.Status.cancelled: 0,
}


def compute_priority_score(task: models.Task) -> int:
    score = PRIORITY_SCORE.get(task.priority, 0) + STATUS_SCORE.get(task.status, 0)
    if task.due_date:
        now = datetime.utcnow()
        days_until_due = (task.due_date - now).days
        if days_until_due < 0:
            score += 30
        elif days_until_due <= 1:
            score += 20
        elif days_until_due <= 3:
            score += 15
        elif days_until_due <= 7:
            score += 10
    return score


def get_prioritized_tasks(db: Session, limit: int = 10) -> List[dict]:
    tasks = db.query(models.Task).filter(
        models.Task.status.in_([models.Status.todo, models.Status.in_progress])
    ).all()
    scored = [
        {"task": t, "priority_score": compute_priority_score(t)}
        for t in tasks
    ]
    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    return scored[:limit]
