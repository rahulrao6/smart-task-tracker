"""Integration tests for task API endpoints."""
import pytest
from httpx import AsyncClient

from src.app.models import TaskPriority, Project, Tag, Task, TaskStatus


class TestListTasks:
    async def test_list_tasks_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    async def test_list_tasks_returns_all(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    async def test_list_tasks_pagination_page1(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    async def test_list_tasks_pagination_page2(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks?page=2&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 2

    async def test_list_tasks_pagination_last_page(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks?page=3&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 1

    async def test_list_tasks_filter_by_status(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks?status=todo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "todo"

    async def test_list_tasks_filter_by_priority(
        self, client: AsyncClient, multiple_tasks
    ):
        resp = await client.get("/api/v1/tasks?priority=high")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["priority"] == "high"

    async def test_list_tasks_filter_by_project(
        self, client: AsyncClient, multiple_tasks, sample_project
    ):
        resp = await client.get(f"/api/v1/tasks?project_id={sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    async def test_list_tasks_search(self, client: AsyncClient, multiple_tasks):
        resp = await client.get("/api/v1/tasks?search=Search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "Search Me Task" in data["items"][0]["title"]

    async def test_list_tasks_search_case_insensitive(
        self, client: AsyncClient, multiple_tasks
    ):
        resp = await client.get("/api/v1/tasks?search=search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    async def test_list_tasks_filter_by_tag(
        self, client: AsyncClient, sample_task, sample_tag
    ):
        resp_tag = await client.post(
            "/api/v1/tasks",
            json={"title": "Tagged Task", "tag_ids": [sample_tag.id]},
        )
        assert resp_tag.status_code == 201
        task_id = resp_tag.json()["id"]

        resp = await client.get(f"/api/v1/tasks?tag_id={sample_tag.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == task_id

    async def test_list_tasks_invalid_page(self, client: AsyncClient):
        resp = await client.get("/api/v1/tasks?page=0")
        assert resp.status_code == 422

    async def test_list_tasks_invalid_page_size(self, client: AsyncClient):
        resp = await client.get("/api/v1/tasks?page_size=200")
        assert resp.status_code == 422

    async def test_list_tasks_combined_filters(
        self, client: AsyncClient, multiple_tasks, sample_project
    ):
        resp = await client.get(
            f"/api/v1/tasks?status=todo&project_id={sample_project.id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "todo"

    async def test_list_tasks_response_has_required_fields(
        self, client: AsyncClient, sample_task
    ):
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        for field in ["id", "title", "status", "priority", "created_at", "updated_at"]:
            assert field in item


class TestCreateTask:
    async def test_create_task_minimal(self, client: AsyncClient):
        resp = await client.post("/api/v1/tasks", json={"title": "New Task"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["title"] == "New Task"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert data["tags"] == []
        assert data["project"] is None

    async def test_create_task_full(
        self, client: AsyncClient, sample_project, sample_tag
    ):
        payload = {
            "title": "Full Task",
            "description": "A complete task",
            "status": "in_progress",
            "priority": "high",
            "project_id": sample_project.id,
            "tag_ids": [sample_tag.id],
        }
        resp = await client.post("/api/v1/tasks", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Full Task"
        assert data["description"] == "A complete task"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["project"]["id"] == sample_project.id
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == sample_tag.id

    async def test_create_task_missing_title(self, client: AsyncClient):
        resp = await client.post("/api/v1/tasks", json={"description": "No title"})
        assert resp.status_code == 422

    async def test_create_task_empty_title(self, client: AsyncClient):
        resp = await client.post("/api/v1/tasks", json={"title": ""})
        assert resp.status_code == 422

    async def test_create_task_invalid_priority(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tasks", json={"title": "Task", "priority": "extreme"}
        )
        assert resp.status_code == 422

    async def test_create_task_invalid_status(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tasks", json={"title": "Task", "status": "unknown"}
        )
        assert resp.status_code == 422

    async def test_create_task_nonexistent_tag(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tasks", json={"title": "Task", "tag_ids": [9999]}
        )
        assert resp.status_code == 404

    async def test_create_task_with_multiple_tags(
        self, client: AsyncClient, sample_tag, sample_tag2
    ):
        resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Multi-tag task", "tag_ids": [sample_tag.id, sample_tag2.id]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["tags"]) == 2

    async def test_create_task_with_due_date(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Due task", "due_date": "2025-12-31T23:59:00"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["due_date"] is not None

    async def test_create_task_all_priorities(self, client: AsyncClient):
        for priority in ["low", "medium", "high", "urgent"]:
            resp = await client.post(
                "/api/v1/tasks",
                json={"title": f"Task {priority}", "priority": priority},
            )
            assert resp.status_code == 201
            assert resp.json()["priority"] == priority

    async def test_create_task_all_statuses(self, client: AsyncClient):
        for s in ["todo", "in_progress", "done", "cancelled"]:
            resp = await client.post(
                "/api/v1/tasks", json={"title": f"Task {s}", "status": s}
            )
            assert resp.status_code == 201
            assert resp.json()["status"] == s

    async def test_create_task_returns_timestamps(self, client: AsyncClient):
        resp = await client.post("/api/v1/tasks", json={"title": "Timestamped"})
        assert resp.status_code == 201
        data = resp.json()
        assert "created_at" in data
        assert "updated_at" in data


class TestGetTask:
    async def test_get_task_success(self, client: AsyncClient, sample_task):
        resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_task.id
        assert data["title"] == sample_task.title

    async def test_get_task_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/tasks/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_get_task_includes_project(
        self, client: AsyncClient, sample_task, sample_project
    ):
        resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] is not None
        assert data["project"]["id"] == sample_project.id

    async def test_get_task_includes_tags(
        self, client: AsyncClient, sample_task, sample_tag
    ):
        await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"tag_ids": [sample_tag.id]}
        )
        resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "bug"

    async def test_get_task_no_tags_returns_empty_list(
        self, client: AsyncClient, sample_task
    ):
        resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        data = resp.json()
        assert data["tags"] == []


class TestUpdateTask:
    async def test_update_task_title(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"title": "Updated Title"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    async def test_update_task_status(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"status": "in_progress"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    async def test_update_task_priority(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"priority": "urgent"}
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "urgent"

    async def test_update_task_to_done_sets_completed_at(
        self, client: AsyncClient, sample_task
    ):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"status": "done"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

    async def test_update_task_from_done_clears_completed_at(
        self, client: AsyncClient, sample_task
    ):
        await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"status": "done"}
        )
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"status": "todo"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "todo"
        assert data["completed_at"] is None

    async def test_update_task_tags(
        self, client: AsyncClient, sample_task, sample_tag, sample_tag2
    ):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}",
            json={"tag_ids": [sample_tag.id, sample_tag2.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tags"]) == 2

    async def test_update_task_clear_tags(
        self, client: AsyncClient, sample_task, sample_tag
    ):
        await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"tag_ids": [sample_tag.id]}
        )
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"tag_ids": []}
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == []

    async def test_update_task_nonexistent_tag(
        self, client: AsyncClient, sample_task
    ):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"tag_ids": [9999]}
        )
        assert resp.status_code == 404

    async def test_update_task_not_found(self, client: AsyncClient):
        resp = await client.patch("/api/v1/tasks/99999", json={"title": "Ghost"})
        assert resp.status_code == 404

    async def test_update_task_partial(self, client: AsyncClient, sample_task):
        original_priority = sample_task.priority
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"title": "Only Title Changed"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Only Title Changed"
        assert data["priority"] == original_priority

    async def test_update_task_project(self, client: AsyncClient, sample_task):
        new_proj_resp = await client.post(
            "/api/v1/projects", json={"name": "New Project"}
        )
        assert new_proj_resp.status_code == 201
        new_proj_id = new_proj_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"project_id": new_proj_id}
        )
        assert resp.status_code == 200
        assert resp.json()["project"]["id"] == new_proj_id

    async def test_update_task_unset_project(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"project_id": None}
        )
        assert resp.status_code == 200
        assert resp.json()["project"] is None

    async def test_update_task_invalid_status(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"status": "invalid"}
        )
        assert resp.status_code == 422

    async def test_update_task_description(self, client: AsyncClient, sample_task):
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"description": "New description"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "New description"


class TestDeleteTask:
    async def test_delete_task_success(self, client: AsyncClient, sample_task):
        resp = await client.delete(f"/api/v1/tasks/{sample_task.id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert get_resp.status_code == 404

    async def test_delete_task_not_found(self, client: AsyncClient):
        resp = await client.delete("/api/v1/tasks/99999")
        assert resp.status_code == 404

    async def test_delete_task_removes_from_list(
        self, client: AsyncClient, multiple_tasks
    ):
        task_id = multiple_tasks[0].id
        await client.delete(f"/api/v1/tasks/{task_id}")
        resp = await client.get("/api/v1/tasks")
        assert resp.json()["total"] == 4

    async def test_delete_task_with_tags_preserves_tags(
        self, client: AsyncClient, sample_task, sample_tag
    ):
        await client.patch(
            f"/api/v1/tasks/{sample_task.id}", json={"tag_ids": [sample_tag.id]}
        )
        await client.delete(f"/api/v1/tasks/{sample_task.id}")
        tag_resp = await client.get(f"/api/v1/tags/{sample_tag.id}")
        assert tag_resp.status_code == 200

    async def test_delete_task_no_body(self, client: AsyncClient, sample_task):
        resp = await client.delete(f"/api/v1/tasks/{sample_task.id}")
        assert resp.status_code == 204
        assert resp.content == b""


class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
