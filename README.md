# Smart Task Tracker

A smart task tracking REST API with AI-powered prioritization. Built with FastAPI and SQLite, it helps teams manage tasks efficiently by automatically scoring and ranking tasks based on priority, status, and due dates.

## Features

- **Full CRUD** — Create, read, update, and delete tasks via a clean REST API
- **AI-powered prioritization** — Automatic priority scoring based on priority level, status, and due date urgency
- **Filtering & search** — Filter tasks by status or priority; full-text search across title and description
- **Pagination** — Efficient pagination for large task lists
- **OpenAPI / Swagger UI** — Interactive API docs at `/docs`, ReDoc at `/redoc`
- **Health endpoint** — `/health` for liveness checks and database connectivity
- **CORS support** — Configurable allowed origins for browser clients
- **SQLite storage** — Zero-configuration database, easy to swap for Postgres

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) 0.111 |
| Server | [Uvicorn](https://www.uvicorn.org/) (ASGI) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 |
| Database | SQLite (default) |
| Validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Config | pydantic-settings + `.env` |
| Testing | pytest + httpx TestClient |
| Container | Docker / docker-compose |

## Setup Instructions

### Prerequisites

- Python 3.11+
- pip

### Install & Run

```bash
# 1. Clone the repo
git clone https://github.com/rahulrao6/smart-task-tracker.git
cd smart-task-tracker

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional)
cp .env.example .env
# Edit .env as needed

# 5. Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Run Tests

```bash
pytest tests/ -v
```

### Docker

```bash
# Build and start with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down
```

The app will be available at `http://localhost:8000`.

## API Reference

Base URL: `/api/v1`

### Tasks

#### `GET /api/v1/tasks/`

List all tasks with optional filtering and pagination.

| Query Param | Type | Description |
|---|---|---|
| `skip` | int | Records to skip (default: 0) |
| `limit` | int | Max records (default: 100, max: 500) |
| `status` | string | Filter by status: `todo`, `in_progress`, `done`, `cancelled` |
| `priority` | string | Filter by priority: `low`, `medium`, `high`, `critical` |
| `search` | string | Full-text search in title and description |

**Response 200:**
```json
{
  "tasks": [...],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

---

#### `POST /api/v1/tasks/`

Create a new task.

**Request body:**
```json
{
  "title": "Deploy v2.0",
  "description": "Roll out the new release to production",
  "priority": "high",
  "status": "todo",
  "due_date": "2024-12-31T23:59:00",
  "tags": "deploy,release"
}
```

**Response 201:** Returns the created task object.

---

#### `GET /api/v1/tasks/prioritized`

Returns active tasks sorted by computed priority score (highest first). Only includes tasks in `todo` or `in_progress` status.

| Query Param | Type | Description |
|---|---|---|
| `limit` | int | Max tasks to return (default: 10, max: 100) |

**Response 200:**
```json
[
  {
    "id": 7,
    "title": "Fix production outage",
    "priority": "critical",
    "status": "in_progress",
    "priority_score": 90,
    "..."
  }
]
```

Priority score formula:
- Priority level: `critical=40`, `high=30`, `medium=20`, `low=10`
- Status bonus: `in_progress=+20`, `todo=+10`
- Overdue: `+30`, due within 1 day: `+20`, within 3 days: `+15`, within 7 days: `+10`

---

#### `GET /api/v1/tasks/{task_id}`

Get a single task by ID.

**Response 200:** Task object.
**Response 404:** Task not found.

---

#### `PATCH /api/v1/tasks/{task_id}`

Partially update a task. All fields are optional.

**Request body:** Any subset of task fields (`title`, `description`, `status`, `priority`, `due_date`, `tags`).

**Response 200:** Updated task object.
**Response 404:** Task not found.

---

#### `DELETE /api/v1/tasks/{task_id}`

Delete a task.

**Response 204:** No content.
**Response 404:** Task not found.

---

### Health

#### `GET /health`

Health check endpoint. Returns app version and database connectivity status.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

---

### Task Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | int | — | Auto-generated |
| `title` | string | Yes | Task title (1–255 chars) |
| `description` | string | No | Detailed description |
| `status` | enum | No | `todo` \| `in_progress` \| `done` \| `cancelled` (default: `todo`) |
| `priority` | enum | No | `low` \| `medium` \| `high` \| `critical` (default: `medium`) |
| `due_date` | datetime | No | ISO 8601 due date |
| `tags` | string | No | Comma-separated tags (max 500 chars) |
| `created_at` | datetime | — | Auto-set on creation |
| `updated_at` | datetime | — | Auto-updated on change |

## Architecture Overview

```
smart-task-tracker/
├── app/
│   ├── main.py          # FastAPI app, CORS, router registration, /health
│   ├── config.py        # Settings via pydantic-settings + .env
│   ├── database.py      # SQLAlchemy engine, session factory, Base
│   ├── models.py        # SQLAlchemy ORM models (Task, enums)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database operations + priority scoring logic
│   └── routers/
│       └── tasks.py     # /api/v1/tasks route handlers
├── tests/
│   ├── conftest.py      # pytest fixtures (in-memory test DB, TestClient)
│   └── test_tasks.py    # API integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

**Request flow:**

```
HTTP Request
    → FastAPI (main.py)
    → Router (routers/tasks.py)
    → CRUD layer (crud.py)
    → SQLAlchemy ORM (models.py)
    → SQLite (tasks.db)
```

The application follows a layered architecture:
- **Routers** handle HTTP concerns (request parsing, response codes)
- **CRUD** encapsulates all database queries and business logic
- **Models** define the database schema
- **Schemas** define API contracts (input validation + output serialization)
- **Config** centralizes all settings, loaded from environment variables

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Smart Task Tracker` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./tasks.db` | SQLAlchemy database URL |
| `SECRET_KEY` | `changeme-in-production` | Secret key for security |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowed origins |
