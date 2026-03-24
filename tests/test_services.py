"""Unit tests for priority and analytics services."""
import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.app.models import TaskPriority, TaskStatus
from src.app.services.analytics import get_productivity_stats, get_summary_stats
from src.app.services.priority import (
    _due_date_score,
    _staleness_score,
    get_smart_priority_list,
    score_task,
)


def _make_task(
    title: str = "Test Task",
    status: TaskStatus = TaskStatus.todo,
    priority: TaskPriority = TaskPriority.medium,
    due_date: datetime | None = None,
    completed_at: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> SimpleNamespace:
    now = datetime.now(tz=timezone.utc)
    return SimpleNamespace(
        id=1,
        title=title,
        status=status,
        priority=priority,
        due_date=due_date,
        completed_at=completed_at,
        created_at=created_at or now,
        updated_at=updated_at or now,
        description=None,
        project_id=None,
    )


class TestDueDateScore:
    def test_no_due_date_returns_zero(self):
        task = _make_task()
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 0

    def test_overdue_returns_50(self):
        task = _make_task(due_date=datetime.now(tz=timezone.utc) - timedelta(days=1))
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 50

    def test_due_within_24h_returns_40(self):
        task = _make_task(
            due_date=datetime.now(tz=timezone.utc) + timedelta(hours=12)
        )
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 40

    def test_due_within_3_days_returns_30(self):
        task = _make_task(
            due_date=datetime.now(tz=timezone.utc) + timedelta(days=2)
        )
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 30

    def test_due_within_7_days_returns_20(self):
        task = _make_task(
            due_date=datetime.now(tz=timezone.utc) + timedelta(days=5)
        )
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 20

    def test_due_within_30_days_returns_10(self):
        task = _make_task(
            due_date=datetime.now(tz=timezone.utc) + timedelta(days=15)
        )
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 10

    def test_due_beyond_30_days_returns_0(self):
        task = _make_task(
            due_date=datetime.now(tz=timezone.utc) + timedelta(days=60)
        )
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 0

    def test_naive_due_date_treated_as_utc(self):
        naive_due = datetime.utcnow() - timedelta(days=1)
        task = _make_task(due_date=naive_due)
        now = datetime.now(tz=timezone.utc)
        assert _due_date_score(task, now) == 50


class TestStalenessScore:
    def test_updated_recently_returns_zero(self):
        task = _make_task(updated_at=datetime.now(tz=timezone.utc) - timedelta(days=1))
        now = datetime.now(tz=timezone.utc)
        assert _staleness_score(task, now) == 0

    def test_updated_8_days_ago_returns_3(self):
        task = _make_task(
            updated_at=datetime.now(tz=timezone.utc) - timedelta(days=8)
        )
        now = datetime.now(tz=timezone.utc)
        assert _staleness_score(task, now) == 3

    def test_updated_15_days_ago_returns_6(self):
        task = _make_task(
            updated_at=datetime.now(tz=timezone.utc) - timedelta(days=15)
        )
        now = datetime.now(tz=timezone.utc)
        assert _staleness_score(task, now) == 6

    def test_updated_31_days_ago_returns_10(self):
        task = _make_task(
            updated_at=datetime.now(tz=timezone.utc) - timedelta(days=31)
        )
        now = datetime.now(tz=timezone.utc)
        assert _staleness_score(task, now) == 10

    def test_naive_updated_at_treated_as_utc(self):
        naive_updated = datetime.utcnow() - timedelta(days=35)
        task = _make_task(updated_at=naive_updated)
        now = datetime.now(tz=timezone.utc)
        assert _staleness_score(task, now) == 10


class TestScoreTask:
    def test_urgent_priority_contributes_40(self):
        task = _make_task(priority=TaskPriority.critical)
        score = score_task(task)
        assert score >= 40

    def test_high_priority_contributes_30(self):
        task = _make_task(priority=TaskPriority.high)
        score = score_task(task)
        assert score >= 30

    def test_medium_priority_contributes_15(self):
        task = _make_task(priority=TaskPriority.medium)
        score = score_task(task)
        assert score >= 15

    def test_low_priority_contributes_5(self):
        task = _make_task(priority=TaskPriority.low)
        score = score_task(task)
        assert score >= 5

    def test_overdue_urgent_task_max_score(self):
        task = _make_task(
            priority=TaskPriority.critical,
            due_date=datetime.now(tz=timezone.utc) - timedelta(days=1),
        )
        score = score_task(task)
        assert score >= 90

    def test_no_due_date_no_staleness_score_equals_priority_only(self):
        task = _make_task(
            priority=TaskPriority.medium,
            updated_at=datetime.now(tz=timezone.utc),
        )
        score = score_task(task)
        assert score == 15

    def test_stale_task_gets_higher_score(self):
        recent = _make_task(
            priority=TaskPriority.medium,
            updated_at=datetime.now(tz=timezone.utc),
        )
        stale = _make_task(
            priority=TaskPriority.medium,
            updated_at=datetime.now(tz=timezone.utc) - timedelta(days=40),
        )
        assert score_task(stale) > score_task(recent)


class TestGetSmartPriorityList:
    def test_excludes_done_tasks(self):
        done = _make_task(title="Done", status=TaskStatus.done, priority=TaskPriority.critical)
        todo = _make_task(title="Todo", status=TaskStatus.todo, priority=TaskPriority.low)
        result = get_smart_priority_list([done, todo])
        titles = [r["task"].title for r in result]
        assert "Done" not in titles
        assert "Todo" in titles

    def test_excludes_cancelled_tasks_does_not_filter(self):
        cancelled = _make_task(
            title="Cancelled", status=TaskStatus.cancelled, priority=TaskPriority.low
        )
        result = get_smart_priority_list([cancelled])
        assert len(result) == 1

    def test_sorted_by_score_descending(self):
        low = _make_task(title="Low", priority=TaskPriority.low)
        urgent = _make_task(
            title="Urgent",
            priority=TaskPriority.critical,
            due_date=datetime.now(tz=timezone.utc) - timedelta(days=1),
        )
        medium = _make_task(title="Medium", priority=TaskPriority.medium)
        result = get_smart_priority_list([low, medium, urgent])
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_list_returns_empty(self):
        assert get_smart_priority_list([]) == []

    def test_all_done_returns_empty(self):
        tasks = [
            _make_task(title=f"Done {i}", status=TaskStatus.done) for i in range(3)
        ]
        assert get_smart_priority_list(tasks) == []

    def test_result_contains_task_and_score(self):
        task = _make_task(title="My Task", priority=TaskPriority.high)
        result = get_smart_priority_list([task])
        assert len(result) == 1
        assert "task" in result[0]
        assert "score" in result[0]
        assert result[0]["task"].title == "My Task"

    def test_in_progress_tasks_included(self):
        task = _make_task(title="WIP", status=TaskStatus.in_progress)
        result = get_smart_priority_list([task])
        assert len(result) == 1


class TestGetSummaryStats:
    def test_empty_task_list(self):
        stats = get_summary_stats([])
        assert stats["total"] == 0
        assert stats["overdue_count"] == 0
        assert stats["avg_completion_time_hours"] is None
        for status in ["todo", "in_progress", "done", "cancelled"]:
            assert stats["task_counts"][status] == 0

    def test_counts_by_status(self):
        tasks = [
            _make_task(status=TaskStatus.todo),
            _make_task(status=TaskStatus.todo),
            _make_task(status=TaskStatus.in_progress),
            _make_task(status=TaskStatus.done),
        ]
        stats = get_summary_stats(tasks)
        assert stats["total"] == 4
        assert stats["task_counts"]["todo"] == 2
        assert stats["task_counts"]["in_progress"] == 1
        assert stats["task_counts"]["done"] == 1

    def test_overdue_count(self):
        overdue = _make_task(
            status=TaskStatus.todo,
            due_date=datetime.now(tz=timezone.utc) - timedelta(days=1),
        )
        future = _make_task(
            status=TaskStatus.todo,
            due_date=datetime.now(tz=timezone.utc) + timedelta(days=7),
        )
        done_overdue = _make_task(
            status=TaskStatus.done,
            due_date=datetime.now(tz=timezone.utc) - timedelta(days=1),
        )
        stats = get_summary_stats([overdue, future, done_overdue])
        assert stats["overdue_count"] == 1

    def test_avg_completion_time(self):
        created = datetime.now(tz=timezone.utc) - timedelta(hours=10)
        completed = datetime.now(tz=timezone.utc)
        task = _make_task(
            status=TaskStatus.done,
            completed_at=completed,
            created_at=created,
        )
        stats = get_summary_stats([task])
        assert stats["avg_completion_time_hours"] is not None
        assert 9.9 <= stats["avg_completion_time_hours"] <= 10.1

    def test_avg_completion_none_when_no_completed(self):
        task = _make_task(status=TaskStatus.todo)
        stats = get_summary_stats([task])
        assert stats["avg_completion_time_hours"] is None

    def test_done_without_completed_at_excluded_from_avg(self):
        task = _make_task(status=TaskStatus.done, completed_at=None)
        stats = get_summary_stats([task])
        assert stats["avg_completion_time_hours"] is None

    def test_naive_due_date_overdue(self):
        naive_due = datetime.utcnow() - timedelta(days=2)
        task = _make_task(status=TaskStatus.todo, due_date=naive_due)
        stats = get_summary_stats([task])
        assert stats["overdue_count"] == 1


class TestGetProductivityStats:
    def test_empty_list(self):
        stats = get_productivity_stats([])
        assert stats["completed_per_day"] == {}
        assert stats["completed_per_week"] == {}

    def test_non_done_tasks_excluded(self):
        task = _make_task(status=TaskStatus.todo)
        stats = get_productivity_stats([task])
        assert stats["completed_per_day"] == {}

    def test_done_without_completed_at_excluded(self):
        task = _make_task(status=TaskStatus.done, completed_at=None)
        stats = get_productivity_stats([task])
        assert stats["completed_per_day"] == {}

    def test_recent_completed_task_counted(self):
        completed = datetime.now(tz=timezone.utc) - timedelta(days=1)
        task = _make_task(status=TaskStatus.done, completed_at=completed)
        stats = get_productivity_stats([task])
        assert len(stats["completed_per_day"]) == 1

    def test_old_completed_task_excluded(self):
        completed = datetime.now(tz=timezone.utc) - timedelta(days=100)
        task = _make_task(status=TaskStatus.done, completed_at=completed)
        stats = get_productivity_stats([task])
        assert len(stats["completed_per_day"]) == 0
        assert len(stats["completed_per_week"]) == 0

    def test_multiple_tasks_same_day_aggregated(self):
        today = datetime.now(tz=timezone.utc).replace(hour=10)
        tasks = [
            _make_task(status=TaskStatus.done, completed_at=today),
            _make_task(status=TaskStatus.done, completed_at=today),
            _make_task(status=TaskStatus.done, completed_at=today),
        ]
        stats = get_productivity_stats(tasks)
        day_key = today.strftime("%Y-%m-%d")
        assert stats["completed_per_day"][day_key] == 3

    def test_week_key_format(self):
        completed = datetime.now(tz=timezone.utc) - timedelta(days=3)
        task = _make_task(status=TaskStatus.done, completed_at=completed)
        stats = get_productivity_stats([task])
        for key in stats["completed_per_week"]:
            assert "-W" in key

    def test_day_sorted_ascending(self):
        day1 = datetime.now(tz=timezone.utc) - timedelta(days=5)
        day2 = datetime.now(tz=timezone.utc) - timedelta(days=3)
        day3 = datetime.now(tz=timezone.utc) - timedelta(days=1)
        tasks = [
            _make_task(status=TaskStatus.done, completed_at=day3),
            _make_task(status=TaskStatus.done, completed_at=day1),
            _make_task(status=TaskStatus.done, completed_at=day2),
        ]
        stats = get_productivity_stats(tasks)
        keys = list(stats["completed_per_day"].keys())
        assert keys == sorted(keys)

    def test_naive_completed_at_treated_as_utc(self):
        naive_completed = datetime.utcnow() - timedelta(days=1)
        task = _make_task(status=TaskStatus.done, completed_at=naive_completed)
        stats = get_productivity_stats([task])
        assert len(stats["completed_per_day"]) == 1


class TestSummaryStatsNaiveDatetimes:
    def test_naive_created_at_and_completed_at(self):
        naive_created = datetime.utcnow() - timedelta(hours=5)
        naive_completed = datetime.utcnow()
        task = _make_task(
            status=TaskStatus.done,
            completed_at=naive_completed,
            created_at=naive_created,
        )
        stats = get_summary_stats([task])
        assert stats["avg_completion_time_hours"] is not None
        assert 4.9 <= stats["avg_completion_time_hours"] <= 5.1
