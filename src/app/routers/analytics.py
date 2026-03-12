from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.app.services.analytics import get_summary_stats, get_productivity_stats
from src.app.services.priority import get_smart_priority_list
from src.app.store import get_store

router = APIRouter(tags=["analytics"])


@router.get("/api/tasks/smart-priority", response_model=List[Dict[str, Any]])
def smart_priority():
    """Return all non-done tasks sorted by composite urgency score (descending).

    Each item includes all task fields plus an ``urgency_score`` (0–100).
    Score components:
    - Due-date proximity : up to 50 pts
    - Priority level     : up to 40 pts
    - Task staleness     : up to 10 pts
    """
    tasks = list(get_store().values())
    return get_smart_priority_list(tasks)


@router.get("/api/analytics/summary", response_model=Dict[str, Any])
def analytics_summary():
    """Return aggregate summary statistics across all tasks.

    Response fields:
    - ``total``                      : total number of tasks
    - ``task_counts``                : counts per status (todo / in_progress / done)
    - ``overdue_count``              : non-done tasks past their due_date
    - ``avg_completion_time_hours``  : mean hours from creation to completion
                                       (null if no completed tasks)
    """
    tasks = list(get_store().values())
    return get_summary_stats(tasks)


@router.get("/api/analytics/productivity", response_model=Dict[str, Any])
def analytics_productivity():
    """Return productivity metrics for completed tasks.

    Response fields:
    - ``completed_per_day``  : {YYYY-MM-DD -> count} for the last 30 days
    - ``completed_per_week`` : {YYYY-Www   -> count} for the last 12 weeks
    """
    tasks = list(get_store().values())
    return get_productivity_stats(tasks)
