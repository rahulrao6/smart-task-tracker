import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.database import Base


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Status(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(Status), default=Status.todo, nullable=False)
    priority = Column(Enum(Priority), default=Priority.medium, nullable=False)
    due_date = Column(DateTime, nullable=True)
    tags = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
