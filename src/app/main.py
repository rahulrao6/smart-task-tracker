from fastapi import FastAPI

from src.app.routers.tasks import router as tasks_router
from src.app.routers.analytics import router as analytics_router

app = FastAPI(
    title="Smart Task Tracker",
    description="Task tracking API with smart prioritization and analytics.",
    version="1.0.0",
)

app.include_router(tasks_router)
app.include_router(analytics_router)


@app.get("/health")
def health():
    return {"status": "ok"}
