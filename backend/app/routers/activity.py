from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity
from app.schemas import ActivityOut

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def recent_activity(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    query = select(Activity).order_by(Activity.created_at.desc(), Activity.id.desc()).limit(limit)
    return db.scalars(query).all()
