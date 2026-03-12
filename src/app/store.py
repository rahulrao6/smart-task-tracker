"""In-memory task store (shared singleton)."""
from __future__ import annotations

from typing import Dict
from uuid import UUID

from src.app.models import Task

_tasks: Dict[UUID, Task] = {}


def get_store() -> Dict[UUID, Task]:
    return _tasks
