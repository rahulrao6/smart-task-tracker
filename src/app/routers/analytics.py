from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.models import Task
from src.app.services.analytics import get_productivity_stats, get_summary_stats
from src.app.services.priority import get_smart_priority_list

router = APIRouter(tags=["analytics"])


@router.get("/api/tasks/smart-priority", response_model=List[Dict[str, Any]])
async def smart_priority(db: AsyncSession = Depends(get_db)):
    """Return all non-done/non-cancelled tasks sorted by composite urgency score (descending).

    Each item includes all task fields plus an ``urgency_score`` (0–100).
    Score components:
    - Due-date proximity : up to 50 pts
    - Priority level     : up to 40 pts
    - Task staleness     : up to 10 pts
    """
    result = await db.execute(select(Task))
    tasks = list(result.scalars().all())
    return get_smart_priority_list(tasks)


@router.get("/api/analytics/summary", response_model=Dict[str, Any])
async def analytics_summary(db: AsyncSession = Depends(get_db)):
    """Return aggregate summary statistics across all tasks.

    Response fields:
    - ``total``                      : total number of tasks
    - ``task_counts``                : counts per status
    - ``overdue_count``              : non-done/cancelled tasks past their due_date
    - ``avg_completion_time_hours``  : mean hours from creation to last update
                                       for done tasks (null if none)
    """
    result = await db.execute(select(Task))
    tasks = list(result.scalars().all())
    return get_summary_stats(tasks)


@router.get("/api/analytics/productivity", response_model=Dict[str, Any])
async def analytics_productivity(db: AsyncSession = Depends(get_db)):
    """Return productivity metrics for completed tasks.

    Response fields:
    - ``completed_per_day``  : {YYYY-MM-DD -> count} for the last 30 days
    - ``completed_per_week`` : {YYYY-Www   -> count} for the last 12 weeks
    """
    result = await db.execute(select(Task))
    tasks = list(result.scalars().all())
    return get_productivity_stats(tasks)
