import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Project, Tag, Task, Priority, TaskStatus

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    TestSessionLocal = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_engine):
    TestSessionLocal = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(name="Test Project", description="A test project", color="#FF5733")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def sample_tag(db_session: AsyncSession) -> Tag:
    tag = Tag(name="bug", color="#FF0000")
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def sample_tag2(db_session: AsyncSession) -> Tag:
    tag = Tag(name="feature", color="#00FF00")
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def sample_task(db_session: AsyncSession, sample_project: Project) -> Task:
    task = Task(
        title="Fix login bug",
        description="Users cannot log in with email",
        status=TaskStatus.todo,
        priority=Priority.high,
        project_id=sample_project.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def multiple_tasks(db_session: AsyncSession, sample_project: Project) -> list[Task]:
    tasks = [
        Task(title="Task One", status=TaskStatus.todo, priority=Priority.low, project_id=sample_project.id),
        Task(title="Task Two", status=TaskStatus.in_progress, priority=Priority.medium),
        Task(title="Task Three", status=TaskStatus.done, priority=Priority.high, project_id=sample_project.id),
        Task(title="Task Four", status=TaskStatus.cancelled, priority=Priority.urgent),
        Task(title="Search Me Task", status=TaskStatus.todo, priority=Priority.low),
    ]
    for task in tasks:
        db_session.add(task)
    await db_session.commit()
    for task in tasks:
        await db_session.refresh(task)
    return tasks
