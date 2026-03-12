from fastapi import FastAPI

from src.app.routers import projects, tasks

app = FastAPI(title="Smart Task Tracker", version="0.1.0")

app.include_router(tasks.router)
app.include_router(projects.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
