# Smart Task Tracker

A smart task tracking REST API with AI-powered prioritization. Built with FastAPI and SQLite, it helps teams manage tasks efficiently by automatically scoring and ranking tasks based on priority, status, and due dates.

## Features

- **Full CRUD** — Create, read, update, and delete tasks and projects via a clean REST API
- **AI-powered prioritization** — Automatic priority scoring based on priority level, status, and due date urgency
- **Filtering & search** — Filter tasks by status, priority, project, and due date range
- **Pagination** — Efficient pagination for large task lists
- **Analytics** — Summary stats and productivity metrics
- **OpenAPI / Swagger UI** — Interactive API docs at `/docs`, ReDoc at `/redoc`
- **Health endpoint** — `/health` for liveness checks
- **CORS support** — Configurable allowed origins for browser clients
- **SQLite storage** — Zero-configuration database, easy to swap for PostgreSQL

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.111 |
| Server | [Uvicorn](https://www.uvicorn.org/) (ASGI) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 (async) |
| Database | SQLite (default) / PostgreSQL |
| Validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Config | pydantic-settings + `.env` |
| Testing | pytest + httpx |
| Container | Docker / docker-compose |

## Setup Instructions

### Prerequisites

- Python 3.11+
- pip or [uv](https://github.com/astral-sh/uv)

### Install & Run (Local)

```bash
# 1. Clone the repo
git clone https://github.com/rahulrao6/smart-task-tracker.git
cd smart-task-tracker

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"
# or with uv:
# uv sync

# 4. Configure environment (optional)
cp .env.example .env
# Edit .env as needed

# 5. Run the development server
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
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

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Smart Task Tracker` | Application name shown in API docs |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./tasks.db` | Database connection string |
| `SECRET_KEY` | `changeme-in-production` | Secret key for security |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowed origins |

## API Reference

Base URL: `/api`

Interactive documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

### Health

#### `GET /health`

Returns API health status.

**Response 200:**
```json
{ "status": "ok" }
```

---

### Tasks

#### `GET /api/tasks`

List tasks with optional filtering and pagination.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | Filter: `todo`, `in_progress`, `done`, `cancelled` |
| `priority` | string | — | Filter: `low`, `medium`, `high`, `critical` |
| `project_id` | int | — | Filter by project |
| `due_date_from` | datetime | — | Filter tasks due on or after this date (ISO 8601) |
| `due_date_to` | datetime | — | Filter tasks due on or before this date (ISO 8601) |
| `limit` | int | `20` | Max records to return (1–100) |
| `offset` | int | `0` | Records to skip |

**Response 200:**
```json
[
  {
    "id": 1,
    "title": "Design API schema",
    "description": "Define request/response schemas for all endpoints",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59",
    "project_id": 1,
    "tags": [],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

#### `POST /api/tasks`

Create a new task.

**Request body:**
```json
{
  "title": "Design API schema",
  "description": "Define request/response schemas for all endpoints",
  "status": "todo",
  "priority": "high",
  "due_date": "2024-12-31T23:59:59",
  "project_id": 1,
  "tag_ids": [1, 2]
}
```

**Response 201:** Task object (see above)

---

#### `GET /api/tasks/{task_id}`

Get a single task by ID.

**Response 200:** Task object
**Response 404:** `{ "detail": "Task not found" }`

---

#### `PUT /api/tasks/{task_id}`

Update a task (full or partial).

**Request body:** Same fields as `POST /api/tasks` (all optional)

**Response 200:** Updated task object
**Response 404:** `{ "detail": "Task not found" }`

---

#### `DELETE /api/tasks/{task_id}`

Delete a task by ID.

**Response 204:** No content
**Response 404:** `{ "detail": "Task not found" }`

---

#### `GET /api/tasks/smart-priority`

Get tasks ranked by AI-powered priority score. Score is computed from:
- **Priority level** (critical=40, high=30, medium=20, low=10)
- **Due date urgency** (overdue=50pts → due in 7 days=10pts)
- **Staleness** (time since last update, up to 10pts)

| Query Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `10` | Max tasks to return |

**Response 200:**
```json
[
  {
    "id": 1,
    "title": "Fix critical bug",
    "priority_score": 85,
    "...": "..."
  }
]
```

---

### Projects

#### `GET /api/projects`

List all projects.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | `20` | Max records (1–100) |
| `offset` | int | `0` | Records to skip |

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "Backend API",
    "description": "REST API development",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

#### `POST /api/projects`

Create a new project.

**Request body:**
```json
{
  "name": "Backend API",
  "description": "REST API development"
}
```

**Response 201:** Project object

---

#### `GET /api/projects/{project_id}`

Get a project with its nested tasks.

**Response 200:** Project object with `tasks` array
**Response 404:** `{ "detail": "Project not found" }`

---

#### `PUT /api/projects/{project_id}`

Update a project.

**Response 200:** Updated project object
**Response 404:** `{ "detail": "Project not found" }`

---

#### `DELETE /api/projects/{project_id}`

Delete a project.

**Response 204:** No content
**Response 404:** `{ "detail": "Project not found" }`

---

### Analytics

#### `GET /api/analytics/summary`

Get summary statistics across all tasks.

**Response 200:**
```json
{
  "total": 42,
  "by_status": {
    "todo": 10,
    "in_progress": 5,
    "done": 25,
    "cancelled": 2
  },
  "overdue_count": 3,
  "avg_completion_time_hours": 48.5
}
```

---

#### `GET /api/analytics/productivity`

Get productivity metrics over a time window.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | `7` | Look-back window in days |

**Response 200:**
```json
{
  "completed_last_day": 2,
  "completed_last_week": 8,
  "period_days": 7
}
```

---

## Data Models

### Task Status

| Value | Description |
|---|---|
| `todo` | Not yet started |
| `in_progress` | Currently being worked on |
| `done` | Completed |
| `cancelled` | Cancelled |

### Task Priority

| Value | Score | Description |
|---|---|---|
| `low` | 10 | Nice to have |
| `medium` | 20 | Standard priority |
| `high` | 30 | Should be done soon |
| `critical` | 40 | Blocking / urgent |

## Architecture

```
src/
└── app/
    ├── main.py          # FastAPI app, middleware, router registration
    ├── models.py        # SQLAlchemy ORM models (Task, Project, Tag)
    ├── schemas.py       # Pydantic request/response schemas
    ├── database.py      # Async SQLAlchemy engine and session factory
    ├── services/
    │   ├── priority.py  # AI prioritization scoring logic
    │   └── analytics.py # Summary and productivity analytics
    └── routers/
        ├── tasks.py     # Task CRUD + smart-priority endpoint
        ├── projects.py  # Project CRUD
        └── analytics.py # Analytics endpoints
tests/                   # pytest integration tests
pyproject.toml           # Project metadata and dependencies
Dockerfile               # Container image
docker-compose.yml       # Multi-service orchestration
.env.example             # Environment variable reference
```

## License

MIT
