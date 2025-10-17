"""Health Check Endpoint"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.base import get_db
from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    environment: str
    database: str


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.

    Returns application status and database connectivity.
    """
    # Test database connection
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        environment=settings.env,
        database=db_status,
    )
