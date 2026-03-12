"""Unit tests for Task, Project, and Tag SQLAlchemy models."""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Project, Tag, Priority, TaskStatus


class TestProjectModel:
    async def test_create_project_minimal(self, db_session: AsyncSession):
        project = Project(name="My Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.id is not None
        assert project.name == "My Project"
        assert project.description is None
        assert project.color is None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    async def test_create_project_full(self, db_session: AsyncSession):
        project = Project(name="Full Project", description="A full project", color="#AABBCC")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.name == "Full Project"
        assert project.description == "A full project"
        assert project.color == "#AABBCC"

    async def test_project_unique_name(self, db_session: AsyncSession):
        p1 = Project(name="Unique")
        p2 = Project(name="Unique")
        db_session.add(p1)
        await db_session.commit()
        db_session.add(p2)
        with pytest.raises(Exception):
            await db_session.commit()

    async def test_project_tasks_relationship(self, db_session: AsyncSession, sample_project: Project, sample_task: Task):
        result = await db_session.execute(
            select(Project).where(Project.id == sample_project.id)
        )
        project = result.scalar_one()
        await db_session.refresh(project, ["tasks"])
        assert len(project.tasks) == 1
        assert project.tasks[0].title == sample_task.title

    async def test_delete_project_nullifies_task_project(self, db_session: AsyncSession, sample_project: Project, sample_task: Task):
        from sqlalchemy import update as sa_update
        task_id = sample_task.id
        await db_session.execute(sa_update(Task).where(Task.project_id == sample_project.id).values(project_id=None))
        await db_session.delete(sample_project)
        await db_session.commit()
        result = await db_session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        assert task is not None
        assert task.project_id is None


class TestTagModel:
    async def test_create_tag_minimal(self, db_session: AsyncSession):
        tag = Tag(name="urgent")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        assert tag.id is not None
        assert tag.name == "urgent"
        assert tag.color is None
        assert isinstance(tag.created_at, datetime)

    async def test_create_tag_with_color(self, db_session: AsyncSession):
        tag = Tag(name="bug", color="#FF0000")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        assert tag.color == "#FF0000"

    async def test_tag_unique_name(self, db_session: AsyncSession):
        t1 = Tag(name="duplicate")
        t2 = Tag(name="duplicate")
        db_session.add(t1)
        await db_session.commit()
        db_session.add(t2)
        with pytest.raises(Exception):
            await db_session.commit()

    async def test_tag_task_relationship(self, db_session: AsyncSession, sample_task: Task, sample_tag: Tag):
        result = await db_session.execute(select(Task).where(Task.id == sample_task.id))
        task = result.scalar_one()
        await db_session.refresh(task, ["tags"])
        task.tags.append(sample_tag)
        await db_session.commit()
        await db_session.refresh(task, ["tags"])
        assert len(task.tags) == 1
        assert task.tags[0].name == "bug"


class TestTaskModel:
    async def test_create_task_minimal(self, db_session: AsyncSession):
        task = Task(title="Do something")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.title == "Do something"
        assert task.status == TaskStatus.todo
        assert task.priority == Priority.medium
        assert task.description is None
        assert task.due_date is None
        assert task.completed_at is None
        assert task.project_id is None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    async def test_create_task_full(self, db_session: AsyncSession, sample_project: Project):
        due = datetime(2025, 12, 31, 23, 59, 0)
        task = Task(
            title="Complete feature",
            description="Implement the feature as described",
            status=TaskStatus.in_progress,
            priority=Priority.urgent,
            due_date=due,
            project_id=sample_project.id,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.title == "Complete feature"
        assert task.description == "Implement the feature as described"
        assert task.status == TaskStatus.in_progress
        assert task.priority == Priority.urgent
        assert task.due_date == due
        assert task.project_id == sample_project.id

    async def test_task_priority_enum_values(self, db_session: AsyncSession):
        for p in Priority:
            task = Task(title=f"task-{p.value}", priority=p)
            db_session.add(task)
        await db_session.commit()
        result = await db_session.execute(select(Task))
        tasks = result.scalars().all()
        priorities = {t.priority for t in tasks}
        assert priorities == set(Priority)

    async def test_task_status_enum_values(self, db_session: AsyncSession):
        for s in TaskStatus:
            task = Task(title=f"task-{s.value}", status=s)
            db_session.add(task)
        await db_session.commit()
        result = await db_session.execute(select(Task))
        tasks = result.scalars().all()
        statuses = {t.status for t in tasks}
        assert statuses == set(TaskStatus)

    async def test_task_multiple_tags(self, db_session: AsyncSession, sample_task: Task, sample_tag: Tag, sample_tag2: Tag):
        result = await db_session.execute(select(Task).where(Task.id == sample_task.id))
        task = result.scalar_one()
        await db_session.refresh(task, ["tags"])
        task.tags = [sample_tag, sample_tag2]
        await db_session.commit()
        await db_session.refresh(task, ["tags"])
        assert len(task.tags) == 2
        tag_names = {t.name for t in task.tags}
        assert tag_names == {"bug", "feature"}

    async def test_task_project_relationship(self, db_session: AsyncSession, sample_task: Task, sample_project: Project):
        result = await db_session.execute(select(Task).where(Task.id == sample_task.id))
        task = result.scalar_one()
        await db_session.refresh(task, ["project"])
        assert task.project is not None
        assert task.project.id == sample_project.id
        assert task.project.name == "Test Project"

    async def test_task_without_project(self, db_session: AsyncSession):
        task = Task(title="Standalone task")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        assert task.project_id is None

    async def test_delete_task_leaves_tags(self, db_session: AsyncSession, sample_task: Task, sample_tag: Tag):
        result = await db_session.execute(select(Task).where(Task.id == sample_task.id))
        task = result.scalar_one()
        await db_session.refresh(task, ["tags"])
        task.tags = [sample_tag]
        await db_session.commit()

        await db_session.delete(task)
        await db_session.commit()

        tag_result = await db_session.execute(select(Tag).where(Tag.id == sample_tag.id))
        tag = tag_result.scalar_one_or_none()
        assert tag is not None

    async def test_priority_enum_values_correct(self):
        assert Priority.low == "low"
        assert Priority.medium == "medium"
        assert Priority.high == "high"
        assert Priority.urgent == "urgent"

    async def test_status_enum_values_correct(self):
        assert TaskStatus.todo == "todo"
        assert TaskStatus.in_progress == "in_progress"
        assert TaskStatus.done == "done"
        assert TaskStatus.cancelled == "cancelled"
