from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import init_db
from app.routers import tasks, projects, tags


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Smart Task Tracker",
    description="A smart task tracking API with AI-powered prioritization.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tasks.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
