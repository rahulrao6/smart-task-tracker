"""Tests for tasks router."""
import pytest
from httpx import AsyncClient
from datetime import date
from uuid import UUID


@pytest.mark.asyncio
class TestCreateTask:
    """Test task creation."""

    async def test_create_task(self, client: AsyncClient):
        """Test creating a task."""
        response = await client.post(
            "/tasks/",
            json={"title": "Test Task", "description": "A test task"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert "id" in data

    async def test_create_task_with_status(self, client: AsyncClient):
        """Test creating a task with custom status."""
        response = await client.post(
            "/tasks/",
            json={"title": "In Progress Task", "status": "in_progress"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "in_progress"

    async def test_create_task_with_priority(self, client: AsyncClient):
        """Test creating a task with priority."""
        response = await client.post(
            "/tasks/",
            json={"title": "Critical Task", "priority": "critical"},
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "critical"

    async def test_create_task_with_due_date(self, client: AsyncClient):
        """Test creating a task with due date."""
        due_date = "2026-12-31"
        response = await client.post(
            "/tasks/",
            json={"title": "Task with deadline", "due_date": due_date},
        )
        assert response.status_code == 201
        assert response.json()["due_date"] == due_date

    async def test_create_task_with_tags(self, client: AsyncClient):
        """Test creating a task with tags."""
        response = await client.post(
            "/tasks/",
            json={"title": "Tagged Task", "tags": ["urgent", "bug"]},
        )
        assert response.status_code == 201
        assert response.json()["tags"] == ["urgent", "bug"]

    async def test_create_task_invalid_status(self, client: AsyncClient):
        """Test creating a task with invalid status."""
        response = await client.post(
            "/tasks/",
            json={"title": "Invalid Status", "status": "invalid"},
        )
        assert response.status_code == 422

    async def test_create_task_invalid_priority(self, client: AsyncClient):
        """Test creating a task with invalid priority."""
        response = await client.post(
            "/tasks/",
            json={"title": "Invalid Priority", "priority": "invalid"},
        )
        assert response.status_code == 422

    async def test_create_task_empty_title(self, client: AsyncClient):
        """Test creating a task with empty title."""
        response = await client.post("/tasks/", json={"title": ""})
        assert response.status_code == 422

    async def test_create_task_title_too_long(self, client: AsyncClient):
        """Test creating a task with title exceeding max length."""
        response = await client.post(
            "/tasks/", json={"title": "x" * 256}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListTasks:
    """Test listing tasks."""

    async def test_list_tasks_empty(self, client: AsyncClient):
        """Test listing tasks when empty."""
        response = await client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["limit"] == 20
        assert data["offset"] == 0

    async def test_list_tasks_with_items(self, client: AsyncClient):
        """Test listing tasks with items."""
        create_response = await client.post("/tasks/", json={"title": "Task 1"})
        task_id = create_response.json()["id"]

        response = await client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == task_id

    async def test_list_tasks_filter_by_status(self, client: AsyncClient):
        """Test filtering tasks by status."""
        await client.post("/tasks/", json={"title": "Todo Task", "status": "todo"})
        await client.post(
            "/tasks/", json={"title": "Done Task", "status": "done"}
        )

        response = await client.get("/tasks/?status=done")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["title"] == "Done Task"

    async def test_list_tasks_filter_by_priority(self, client: AsyncClient):
        """Test filtering tasks by priority."""
        await client.post("/tasks/", json={"title": "Low", "priority": "low"})
        await client.post(
            "/tasks/", json={"title": "Critical", "priority": "critical"}
        )

        response = await client.get("/tasks/?priority=critical")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["title"] == "Critical"

    async def test_list_tasks_filter_by_due_date_range(self, client: AsyncClient):
        """Test filtering tasks by due date range."""
        await client.post(
            "/tasks/", json={"title": "Task1", "due_date": "2026-01-01"}
        )
        await client.post(
            "/tasks/", json={"title": "Task2", "due_date": "2026-06-01"}
        )
        await client.post(
            "/tasks/", json={"title": "Task3", "due_date": "2026-12-01"}
        )

        # Filter tasks from 2026-01-01 to 2026-06-01
        response = await client.get(
            "/tasks/?due_date_from=2026-01-01&due_date_to=2026-06-01"
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2

    async def test_list_tasks_pagination(self, client: AsyncClient):
        """Test task pagination."""
        for i in range(3):
            await client.post("/tasks/", json={"title": f"Task {i}"})

        response = await client.get("/tasks/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

        response = await client.get("/tasks/?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    async def test_list_tasks_invalid_status_filter(self, client: AsyncClient):
        """Test listing with invalid status filter."""
        response = await client.get("/tasks/?status=invalid")
        assert response.status_code == 422

    async def test_list_tasks_invalid_priority_filter(self, client: AsyncClient):
        """Test listing with invalid priority filter."""
        response = await client.get("/tasks/?priority=invalid")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetTask:
    """Test getting a single task."""

    async def test_get_task(self, client: AsyncClient):
        """Test getting a task by ID."""
        create_response = await client.post("/tasks/", json={"title": "Test Task"})
        task_id = create_response.json()["id"]

        response = await client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"

    async def test_get_nonexistent_task(self, client: AsyncClient):
        """Test getting a nonexistent task."""
        response = await client.get(
            "/tasks/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateTask:
    """Test updating tasks."""

    async def test_update_task_title(self, client: AsyncClient):
        """Test updating task title."""
        create_response = await client.post("/tasks/", json={"title": "Original"})
        task_id = create_response.json()["id"]

        response = await client.put(f"/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_update_task_status(self, client: AsyncClient):
        """Test updating task status."""
        create_response = await client.post(
            "/tasks/", json={"title": "Test", "status": "todo"}
        )
        task_id = create_response.json()["id"]

        response = await client.put(f"/tasks/{task_id}", json={"status": "done"})
        assert response.status_code == 200
        assert response.json()["status"] == "done"

    async def test_update_task_priority(self, client: AsyncClient):
        """Test updating task priority."""
        create_response = await client.post("/tasks/", json={"title": "Test"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/tasks/{task_id}", json={"priority": "critical"}
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "critical"

    async def test_update_task_due_date(self, client: AsyncClient):
        """Test updating task due date."""
        create_response = await client.post("/tasks/", json={"title": "Test"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/tasks/{task_id}", json={"due_date": "2026-12-31"}
        )
        assert response.status_code == 200
        assert response.json()["due_date"] == "2026-12-31"

    async def test_update_task_tags(self, client: AsyncClient):
        """Test updating task tags."""
        create_response = await client.post("/tasks/", json={"title": "Test"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/tasks/{task_id}", json={"tags": ["new", "tags"]}
        )
        assert response.status_code == 200
        assert response.json()["tags"] == ["new", "tags"]

    async def test_update_task_invalid_status(self, client: AsyncClient):
        """Test updating with invalid status."""
        create_response = await client.post("/tasks/", json={"title": "Test"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/tasks/{task_id}", json={"status": "invalid"}
        )
        assert response.status_code == 422

    async def test_update_task_invalid_priority(self, client: AsyncClient):
        """Test updating with invalid priority."""
        create_response = await client.post("/tasks/", json={"title": "Test"})
        task_id = create_response.json()["id"]

        response = await client.put(
            f"/tasks/{task_id}", json={"priority": "invalid"}
        )
        assert response.status_code == 422

    async def test_update_nonexistent_task(self, client: AsyncClient):
        """Test updating a nonexistent task."""
        response = await client.put(
            "/tasks/00000000-0000-0000-0000-000000000000",
            json={"title": "Updated"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteTask:
    """Test deleting tasks."""

    async def test_delete_task(self, client: AsyncClient):
        """Test deleting a task."""
        create_response = await client.post("/tasks/", json={"title": "To Delete"})
        task_id = create_response.json()["id"]

        response = await client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_task(self, client: AsyncClient):
        """Test deleting a nonexistent task."""
        response = await client.delete(
            "/tasks/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
