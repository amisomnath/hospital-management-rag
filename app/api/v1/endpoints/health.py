"""Health and readiness endpoints."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DatabaseSession
from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check() -> dict[str, str]:
    """Return a lightweight liveness response."""

    settings = get_settings()
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/ready")
def readiness_check(db: DatabaseSession) -> dict[str, str]:
    """Check that the database can answer a simple query."""

    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
