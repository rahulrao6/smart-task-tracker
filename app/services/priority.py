"""Smart task prioritization service.

Scoring model (higher score = higher urgency):

1. Due-date proximity (0–50 pts)
   - Overdue               : 50
   - Due within 24 h       : 40
   - Due within 3 days     : 30
   - Due within 7 days     : 20
   - Due within 30 days    : 10
   - No due date / >30 days: 0

2. Priority level (0–40 pts)
   - urgent   : 40
   - high     : 30
   - medium   : 15
   - low      : 5

3. Staleness (0–10 pts)
   - Updated > 30 days ago : 10
   - Updated 14–30 days ago: 6
   - Updated 7–14 days ago : 3
   - Updated < 7 days ago  : 0
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.models import Task, Priority, TaskStatus

_PRIORITY_SCORE = {
    Priority.urgent: 40,
    Priority.high: 30,
    Priority.medium: 15,
    Priority.low: 5,
}


def _due_date_score(task: Task, now: datetime) -> int:
    if task.due_date is None:
        return 0

    due = task.due_date
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)

    delta_days = (due - now).total_seconds() / 86_400

    if delta_days < 0:
        return 50
    if delta_days <= 1:
        return 40
    if delta_days <= 3:
        return 30
    if delta_days <= 7:
        return 20
    if delta_days <= 30:
        return 10
    return 0


def _staleness_score(task: Task, now: datetime) -> int:
    updated = task.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    days_since_update = (now - updated).total_seconds() / 86_400

    if days_since_update > 30:
        return 10
    if days_since_update > 14:
        return 6
    if days_since_update > 7:
        return 3
    return 0


def score_task(task: Task) -> int:
    """Return a composite urgency score for task (higher = more urgent)."""
    now = datetime.now(tz=timezone.utc)
    return (
        _due_date_score(task, now)
        + _PRIORITY_SCORE.get(task.priority, 0)
        + _staleness_score(task, now)
    )


def get_smart_priority_list(tasks: List[Task]) -> List[dict]:
    """Return tasks sorted by urgency score (descending), excluding done tasks."""
    active = [t for t in tasks if t.status != TaskStatus.done]
    scored = [{"task": t, "score": score_task(t)} for t in active]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return [{"task": item["task"], "score": item["score"]} for item in scored]
