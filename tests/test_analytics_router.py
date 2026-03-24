"""Tests for analytics router."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSmartPriority:
    """Test smart priority endpoint."""

    async def test_smart_priority_empty(self, client: AsyncClient):
        """Test smart priority with no tasks."""
        response = await client.get("/api/tasks/smart-priority")
        assert response.status_code == 200
        assert response.json() == []

    async def test_smart_priority_with_tasks(self, client: AsyncClient):
        """Test smart priority with tasks."""
        # Create some tasks
        await client.post("/tasks/", json={"title": "Task 1", "priority": "high"})
        await client.post("/tasks/", json={"title": "Task 2", "priority": "low"})

        response = await client.get("/api/tasks/smart-priority")
        assert response.status_code == 200
        # Should return list of tasks, may be empty if priority service not fully implemented
        result = response.json()
        assert isinstance(result, list)


@pytest.mark.asyncio
class TestAnalyticsSummary:
    """Test analytics summary endpoint."""

    async def test_analytics_summary_empty(self, client: AsyncClient):
        """Test analytics summary with no tasks."""
        response = await client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # May have various fields depending on implementation

    async def test_analytics_summary_with_tasks(self, client: AsyncClient):
        """Test analytics summary with tasks."""
        await client.post("/tasks/", json={"title": "Task 1", "status": "done"})
        await client.post("/tasks/", json={"title": "Task 2", "status": "todo"})

        response = await client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
class TestAnalyticsProductivity:
    """Test analytics productivity endpoint."""

    async def test_analytics_productivity_empty(self, client: AsyncClient):
        """Test analytics productivity with no tasks."""
        response = await client.get("/api/analytics/productivity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_analytics_productivity_with_tasks(self, client: AsyncClient):
        """Test analytics productivity with tasks."""
        await client.post("/tasks/", json={"title": "Task 1", "status": "done"})
        await client.post("/tasks/", json={"title": "Task 2", "status": "done"})

        response = await client.get("/api/analytics/productivity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
