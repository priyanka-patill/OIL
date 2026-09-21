from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.database import get_db
from backend.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint confirming system operational status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }
