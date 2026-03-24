"""Tests for projects router."""
import pytest
from httpx import AsyncClient
from uuid import UUID


@pytest.mark.asyncio
class TestCreateProject:
    """Test project creation."""

    async def test_create_project(self, client: AsyncClient):
        """Test creating a project."""
        response = await client.post(
            "/projects/",
            json={"name": "Test Project", "description": "A test project"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert data["status"] == "active"
        assert "id" in data

    async def test_create_project_with_status(self, client: AsyncClient):
        """Test creating a project with custom status."""
        response = await client.post(
            "/projects/",
            json={"name": "Archived Project", "status": "archived"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "archived"

    async def test_create_project_with_tags(self, client: AsyncClient):
        """Test creating a project with tags."""
        response = await client.post(
            "/projects/",
            json={"name": "Tagged Project", "tags": ["urgent", "important"]},
        )
        assert response.status_code == 201
        assert response.json()["tags"] == ["urgent", "important"]

    async def test_create_project_invalid_status(self, client: AsyncClient):
        """Test creating a project with invalid status."""
        response = await client.post(
            "/projects/",
            json={"name": "Invalid Status", "status": "invalid"},
        )
        assert response.status_code == 422

    async def test_create_project_empty_name(self, client: AsyncClient):
        """Test creating a project with empty name."""
        response = await client.post(
            "/projects/",
            json={"name": ""},
        )
        assert response.status_code == 422

    async def test_create_project_name_too_long(self, client: AsyncClient):
        """Test creating a project with name exceeding max length."""
        response = await client.post(
            "/projects/",
            json={"name": "x" * 256},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListProjects:
    """Test listing projects."""

    async def test_list_projects_empty(self, client: AsyncClient):
        """Test listing projects when empty."""
        response = await client.get("/projects/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["limit"] == 20
        assert data["offset"] == 0

    async def test_list_projects_with_items(self, client: AsyncClient):
        """Test listing projects with items."""
        # Create a project
        create_response = await client.post(
            "/projects/", json={"name": "Project 1"}
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # List projects
        response = await client.get("/projects/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == project_id

    async def test_list_projects_filter_by_status(self, client: AsyncClient):
        """Test filtering projects by status."""
        # Create active project
        await client.post("/projects/", json={"name": "Active", "status": "active"})
        # Create archived project
        await client.post("/projects/", json={"name": "Archived", "status": "archived"})

        # Filter by active
        response = await client.get("/projects/?status=active")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["name"] == "Active"

    async def test_list_projects_filter_by_name(self, client: AsyncClient):
        """Test filtering projects by name."""
        await client.post("/projects/", json={"name": "Important Project"})
        await client.post("/projects/", json={"name": "Other Project"})

        response = await client.get("/projects/?name_contains=Important")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["name"] == "Important Project"

    async def test_list_projects_pagination(self, client: AsyncClient):
        """Test project pagination."""
        # Create 3 projects
        for i in range(3):
            await client.post("/projects/", json={"name": f"Project {i}"})

        # Get first page with limit 2
        response = await client.get("/projects/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

        # Get second page
        response = await client.get("/projects/?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    async def test_list_projects_invalid_limit(self, client: AsyncClient):
        """Test listing with invalid limit."""
        response = await client.get("/projects/?limit=0")
        assert response.status_code == 422

    async def test_list_projects_invalid_status_filter(self, client: AsyncClient):
        """Test listing with invalid status filter."""
        response = await client.get("/projects/?status=invalid")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetProject:
    """Test getting a single project."""

    async def test_get_project(self, client: AsyncClient):
        """Test getting a project by ID."""
        create_response = await client.post(
            "/projects/", json={"name": "Test Project"}
        )
        project_id = create_response.json()["id"]

        response = await client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"

    async def test_get_nonexistent_project(self, client: AsyncClient):
        """Test getting a nonexistent project."""
        response = await client.get("/projects/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateProject:
    """Test updating projects."""

    async def test_update_project_name(self, client: AsyncClient):
        """Test updating project name."""
        create_response = await client.post(
            "/projects/", json={"name": "Original"}
        )
        project_id = create_response.json()["id"]

        response = await client.put(
            f"/projects/{project_id}", json={"name": "Updated"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    async def test_update_project_status(self, client: AsyncClient):
        """Test updating project status."""
        create_response = await client.post(
            "/projects/", json={"name": "Test", "status": "active"}
        )
        project_id = create_response.json()["id"]

        response = await client.put(
            f"/projects/{project_id}", json={"status": "archived"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    async def test_update_project_tags(self, client: AsyncClient):
        """Test updating project tags."""
        create_response = await client.post(
            "/projects/", json={"name": "Test"}
        )
        project_id = create_response.json()["id"]

        response = await client.put(
            f"/projects/{project_id}", json={"tags": ["new", "tags"]}
        )
        assert response.status_code == 200
        assert response.json()["tags"] == ["new", "tags"]

    async def test_update_project_invalid_status(self, client: AsyncClient):
        """Test updating with invalid status."""
        create_response = await client.post(
            "/projects/", json={"name": "Test"}
        )
        project_id = create_response.json()["id"]

        response = await client.put(
            f"/projects/{project_id}", json={"status": "invalid"}
        )
        assert response.status_code == 422

    async def test_update_nonexistent_project(self, client: AsyncClient):
        """Test updating a nonexistent project."""
        response = await client.put(
            "/projects/00000000-0000-0000-0000-000000000000",
            json={"name": "Updated"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteProject:
    """Test deleting projects."""

    async def test_delete_project(self, client: AsyncClient):
        """Test deleting a project."""
        create_response = await client.post(
            "/projects/", json={"name": "To Delete"}
        )
        project_id = create_response.json()["id"]

        response = await client.delete(f"/projects/{project_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_project(self, client: AsyncClient):
        """Test deleting a nonexistent project."""
        response = await client.delete(
            "/projects/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
