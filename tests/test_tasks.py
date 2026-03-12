import pytest


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "docs" in data


def test_create_task(client):
    payload = {"title": "Write tests", "priority": "high"}
    response = client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Write tests"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert "id" in data
    assert "created_at" in data


def test_list_tasks_empty(client):
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0


def test_list_tasks(client):
    client.post("/api/v1/tasks/", json={"title": "Task 1"})
    client.post("/api/v1/tasks/", json={"title": "Task 2"})
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["tasks"]) == 2


def test_get_task(client):
    create_resp = client.post("/api/v1/tasks/", json={"title": "My Task", "description": "Details"})
    task_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "My Task"


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/9999")
    assert response.status_code == 404


def test_update_task(client):
    create_resp = client.post("/api/v1/tasks/", json={"title": "Old Title"})
    task_id = create_resp.json()["id"]
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New Title", "status": "in_progress"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "in_progress"


def test_update_task_not_found(client):
    response = client.patch("/api/v1/tasks/9999", json={"title": "X"})
    assert response.status_code == 404


def test_delete_task(client):
    create_resp = client.post("/api/v1/tasks/", json={"title": "To Delete"})
    task_id = create_resp.json()["id"]
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204
    get_resp = client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_delete_task_not_found(client):
    response = client.delete("/api/v1/tasks/9999")
    assert response.status_code == 404


def test_filter_tasks_by_status(client):
    client.post("/api/v1/tasks/", json={"title": "Todo Task", "status": "todo"})
    client.post("/api/v1/tasks/", json={"title": "Done Task", "status": "done"})
    response = client.get("/api/v1/tasks/?status=todo")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["status"] == "todo"


def test_filter_tasks_by_priority(client):
    client.post("/api/v1/tasks/", json={"title": "High Task", "priority": "high"})
    client.post("/api/v1/tasks/", json={"title": "Low Task", "priority": "low"})
    response = client.get("/api/v1/tasks/?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["tasks"][0]["priority"] == "high"


def test_search_tasks(client):
    client.post("/api/v1/tasks/", json={"title": "Deploy to production"})
    client.post("/api/v1/tasks/", json={"title": "Write documentation"})
    response = client.get("/api/v1/tasks/?search=deploy")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "deploy" in data["tasks"][0]["title"].lower()


def test_prioritized_tasks(client):
    client.post("/api/v1/tasks/", json={"title": "Low task", "priority": "low"})
    client.post("/api/v1/tasks/", json={"title": "Critical task", "priority": "critical"})
    client.post("/api/v1/tasks/", json={"title": "High task", "priority": "high"})
    response = client.get("/api/v1/tasks/prioritized")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    assert "priority_score" in tasks[0]
    assert tasks[0]["priority_score"] >= tasks[1]["priority_score"]


def test_create_task_missing_title(client):
    response = client.post("/api/v1/tasks/", json={"description": "No title"})
    assert response.status_code == 422


def test_openapi_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Smart Task Tracker"
