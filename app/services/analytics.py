"""Analytics service for task summary and productivity stats."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from app.models import Task, TaskStatus


def get_summary_stats(tasks: List[Task]) -> dict:
    """Return summary statistics for a list of tasks."""
    now = datetime.now(tz=timezone.utc)

    counts: Dict[str, int] = {s.value: 0 for s in TaskStatus}
    overdue = 0
    completion_times: List[float] = []

    for task in tasks:
        counts[task.status.value] += 1

        if task.status != TaskStatus.done and task.due_date is not None:
            due = task.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                overdue += 1

        if task.status == TaskStatus.done and task.completed_at is not None:
            created = task.created_at
            completed = task.completed_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if completed.tzinfo is None:
                completed = completed.replace(tzinfo=timezone.utc)
            hours = (completed - created).total_seconds() / 3600
            completion_times.append(hours)

    avg_completion_time_hours = (
        round(sum(completion_times) / len(completion_times), 2)
        if completion_times
        else None
    )

    return {
        "total": len(tasks),
        "task_counts": counts,
        "overdue_count": overdue,
        "avg_completion_time_hours": avg_completion_time_hours,
    }


def get_productivity_stats(tasks: List[Task]) -> dict:
    """Return productivity statistics grouped by day and week."""
    now = datetime.now(tz=timezone.utc)
    cutoff_day = now - timedelta(days=30)
    cutoff_week = now - timedelta(weeks=12)

    per_day: Dict[str, int] = defaultdict(int)
    per_week: Dict[str, int] = defaultdict(int)

    for task in tasks:
        if task.status != TaskStatus.done or task.completed_at is None:
            continue

        completed = task.completed_at
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)

        if completed >= cutoff_day:
            day_key = completed.strftime("%Y-%m-%d")
            per_day[day_key] += 1

        if completed >= cutoff_week:
            iso = completed.isocalendar()
            week_key = f"{iso[0]}-W{iso[1]:02d}"
            per_week[week_key] += 1

    return {
        "completed_per_day": dict(sorted(per_day.items())),
        "completed_per_week": dict(sorted(per_week.items())),
    }
