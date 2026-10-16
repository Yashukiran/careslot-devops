from sqlalchemy.orm import Session

from app.models import Activity


def log(db: Session, kind: str, message: str) -> None:
    """Queue an activity entry; it is saved with the caller's commit."""
    db.add(Activity(kind=kind, message=message[:255]))
