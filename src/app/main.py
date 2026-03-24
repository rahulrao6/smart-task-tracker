import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.config import get_settings
from src.app.rate_limit import RateLimitMiddleware
from src.app.routers import projects, tasks
from src.app.routers.analytics import router as analytics_router
from src.app.routers.auth import router as auth_router
from src.app.utils.logging import setup_application_logger

settings = get_settings()

logger = setup_application_logger(
    log_dir=settings.log_dir,
    level=logging.INFO,
    json_format=settings.log_format == "json",
)

app = FastAPI(
    title=settings.app_name,
    description="A smart task tracking API with AI-powered prioritization",
    version=settings.app_version,
)

# Add rate limiting middleware
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests=settings.rate_limit_requests,
        period_seconds=settings.rate_limit_period_seconds,
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(analytics_router)


@app.get("/health", tags=["health"])
def health() -> dict:
    logger.info("Health check requested")
    return {"status": "ok"}
