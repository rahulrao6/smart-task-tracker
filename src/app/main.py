from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.routers import projects, tasks
from src.app.routers.analytics import router as analytics_router

app = FastAPI(
    title="Smart Task Tracker",
    description="A smart task tracking API with AI-powered prioritization",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(analytics_router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
