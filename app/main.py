from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, get_db
from app.routers import tasks
from app import schemas
from sqlalchemy.orm import Session
from fastapi import Depends

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A smart task tracking API with AI-powered prioritization. "
        "Manage tasks with full CRUD operations and automatic priority scoring "
        "based on priority level, status, and due dates."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1")


@app.get("/health", response_model=schemas.HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return schemas.HealthResponse(
        status="ok",
        version=settings.app_version,
        database=db_status,
    )


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
