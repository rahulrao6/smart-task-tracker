"""Integration tests for project and tag API endpoints."""
import pytest
from httpx import AsyncClient

from src.app.models import Project


class TestListProjects:
    async def test_list_projects_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_projects_returns_all(self, client: AsyncClient):
        for i in range(3):
            await client.post("/api/v1/projects", json={"name": f"Project {i}"})
        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_list_projects_order_by_created_desc(self, client: AsyncClient):
        for name in ["Alpha", "Beta", "Gamma"]:
            await client.post("/api/v1/projects", json={"name": name})
        resp = await client.get("/api/v1/projects")
        names = [p["name"] for p in resp.json()]
        assert names == ["Gamma", "Beta", "Alpha"]

    async def test_list_projects_response_fields(self, client: AsyncClient):
        await client.post("/api/v1/projects", json={"name": "Field Test"})
        resp = await client.get("/api/v1/projects")
        item = resp.json()[0]
        for field in ["id", "name", "created_at", "updated_at"]:
            assert field in item


class TestCreateProject:
    async def test_create_project_minimal(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "My Project"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["name"] == "My Project"
        assert data["description"] is None
        assert data["color"] is None
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_project_full(self, client: AsyncClient):
        payload = {
            "name": "Full Project",
            "description": "Detailed description",
            "color": "#123456",
        }
        resp = await client.post("/api/v1/projects", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Full Project"
        assert data["description"] == "Detailed description"
        assert data["color"] == "#123456"

    async def test_create_project_duplicate_name(self, client: AsyncClient):
        await client.post("/api/v1/projects", json={"name": "Duplicate"})
        resp = await client.post("/api/v1/projects", json={"name": "Duplicate"})
        assert resp.status_code == 409

    async def test_create_project_missing_name(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"description": "No name"})
        assert resp.status_code == 422

    async def test_create_project_empty_name(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": ""})
        assert resp.status_code == 422

    async def test_create_project_invalid_color(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/projects", json={"name": "Bad Color", "color": "red"}
        )
        assert resp.status_code == 422

    async def test_create_project_valid_color_formats(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/projects", json={"name": "Color Test", "color": "#AABBCC"}
        )
        assert resp.status_code == 201
        resp2 = await client.post(
            "/api/v1/projects", json={"name": "Color Test 2", "color": "#aabbcc"}
        )
        assert resp2.status_code == 201

    async def test_create_project_name_only_description_null(self, client: AsyncClient):
        resp = await client.post("/api/v1/projects", json={"name": "No Desc"})
        assert resp.status_code == 201
        assert resp.json()["description"] is None


class TestGetProject:
    async def test_get_project_success(self, client: AsyncClient, sample_project):
        resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_project.id
        assert data["name"] == sample_project.name

    async def test_get_project_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/projects/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_get_project_includes_tasks(
        self, client: AsyncClient, sample_project, sample_task
    ):
        resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == sample_task.id

    async def test_get_project_empty_tasks(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        data = resp.json()
        assert isinstance(data["tasks"], list)

    async def test_get_project_tasks_contain_task_fields(
        self, client: AsyncClient, sample_project, sample_task
    ):
        resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        task = resp.json()["tasks"][0]
        assert "id" in task
        assert "title" in task
        assert "status" in task
        assert "priority" in task

    async def test_get_project_includes_color(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        assert resp.status_code == 200
        assert resp.json()["color"] == "#FF5733"


class TestUpdateProject:
    async def test_update_project_name(self, client: AsyncClient, sample_project):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"name": "Renamed Project"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Project"

    async def test_update_project_description(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}",
            json={"description": "New description"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "New description"

    async def test_update_project_color(self, client: AsyncClient, sample_project):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"color": "#000000"}
        )
        assert resp.status_code == 200
        assert resp.json()["color"] == "#000000"

    async def test_update_project_not_found(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/projects/99999", json={"name": "Ghost"}
        )
        assert resp.status_code == 404

    async def test_update_project_duplicate_name(
        self, client: AsyncClient, sample_project
    ):
        other = await client.post("/api/v1/projects", json={"name": "Other Project"})
        assert other.status_code == 201
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"name": "Other Project"}
        )
        assert resp.status_code == 409

    async def test_update_project_same_name_ok(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}",
            json={"name": sample_project.name},
        )
        assert resp.status_code == 200

    async def test_update_project_partial(self, client: AsyncClient, sample_project):
        original_color = sample_project.color
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"description": "Updated"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Updated"
        assert data["color"] == original_color

    async def test_update_project_invalid_color(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"color": "not-a-color"}
        )
        assert resp.status_code == 422

    async def test_update_project_returns_updated_at(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.patch(
            f"/api/v1/projects/{sample_project.id}", json={"description": "Changed"}
        )
        assert resp.status_code == 200
        assert "updated_at" in resp.json()


class TestDeleteProject:
    async def test_delete_project_success(self, client: AsyncClient, sample_project):
        resp = await client.delete(f"/api/v1/projects/{sample_project.id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/projects/{sample_project.id}")
        assert get_resp.status_code == 404

    async def test_delete_project_not_found(self, client: AsyncClient):
        resp = await client.delete("/api/v1/projects/99999")
        assert resp.status_code == 404

    async def test_delete_project_removes_from_list(
        self, client: AsyncClient, sample_project
    ):
        await client.delete(f"/api/v1/projects/{sample_project.id}")
        resp = await client.get("/api/v1/projects")
        assert resp.json() == []

    async def test_delete_project_unlinks_tasks(
        self, client: AsyncClient, sample_project, sample_task
    ):
        await client.delete(f"/api/v1/projects/{sample_project.id}")
        task_resp = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert task_resp.status_code == 200
        assert task_resp.json()["project"] is None
        assert task_resp.json()["project_id"] is None

    async def test_delete_project_no_body(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.delete(f"/api/v1/projects/{sample_project.id}")
        assert resp.status_code == 204
        assert resp.content == b""


class TestTagEndpoints:
    async def test_list_tags_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/tags")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_tag(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tags", json={"name": "backend", "color": "#0000FF"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "backend"
        assert data["color"] == "#0000FF"

    async def test_create_tag_minimal(self, client: AsyncClient):
        resp = await client.post("/api/v1/tags", json={"name": "minimal"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "minimal"
        assert data["color"] is None

    async def test_create_tag_duplicate(self, client: AsyncClient):
        await client.post("/api/v1/tags", json={"name": "mytag"})
        resp = await client.post("/api/v1/tags", json={"name": "mytag"})
        assert resp.status_code == 409

    async def test_create_tag_missing_name(self, client: AsyncClient):
        resp = await client.post("/api/v1/tags", json={"color": "#FF0000"})
        assert resp.status_code == 422

    async def test_create_tag_invalid_color(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/tags", json={"name": "bad", "color": "blue"}
        )
        assert resp.status_code == 422

    async def test_get_tag_success(self, client: AsyncClient, sample_tag):
        resp = await client.get(f"/api/v1/tags/{sample_tag.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "bug"

    async def test_get_tag_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/tags/99999")
        assert resp.status_code == 404

    async def test_update_tag(self, client: AsyncClient, sample_tag):
        resp = await client.patch(
            f"/api/v1/tags/{sample_tag.id}", json={"name": "critical"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "critical"

    async def test_update_tag_color(self, client: AsyncClient, sample_tag):
        resp = await client.patch(
            f"/api/v1/tags/{sample_tag.id}", json={"color": "#FFFFFF"}
        )
        assert resp.status_code == 200
        assert resp.json()["color"] == "#FFFFFF"

    async def test_update_tag_not_found(self, client: AsyncClient):
        resp = await client.patch("/api/v1/tags/99999", json={"name": "x"})
        assert resp.status_code == 404

    async def test_delete_tag_success(self, client: AsyncClient, sample_tag):
        resp = await client.delete(f"/api/v1/tags/{sample_tag.id}")
        assert resp.status_code == 204
        get_resp = await client.get(f"/api/v1/tags/{sample_tag.id}")
        assert get_resp.status_code == 404

    async def test_delete_tag_not_found(self, client: AsyncClient):
        resp = await client.delete("/api/v1/tags/99999")
        assert resp.status_code == 404

    async def test_list_tags_alphabetical(self, client: AsyncClient):
        for name in ["zebra", "apple", "mango"]:
            await client.post("/api/v1/tags", json={"name": name})
        resp = await client.get("/api/v1/tags")
        names = [t["name"] for t in resp.json()]
        assert names == sorted(names)

    async def test_create_tag_returns_id_and_created_at(self, client: AsyncClient):
        resp = await client.post("/api/v1/tags", json={"name": "timestamped"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "created_at" in data
