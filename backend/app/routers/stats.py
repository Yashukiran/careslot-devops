from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, Patient, Priority
from app.schemas import Stats
from app.timeutils import day_range_utc, today_local

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    start, end = day_range_utc(today_local())
    today = (Appointment.start_time >= start) & (Appointment.start_time < end)

    by_status = {s.value: 0 for s in AppointmentStatus}
    rows = db.execute(select(Appointment.status, func.count()).where(today).group_by(Appointment.status))
    for status, count in rows:
        by_status[status.value] = count

    busiest = db.execute(
        select(Doctor.name, func.count(Appointment.id).label("n"))
        .join(Appointment)
        .where(today, Appointment.status != AppointmentStatus.cancelled)
        .group_by(Doctor.name)
        .order_by(func.count(Appointment.id).desc())
        .limit(1)
    ).first()

    return Stats(
        doctors=db.scalar(select(func.count()).select_from(Doctor).where(Doctor.active.is_(True))),
        patients=db.scalar(select(func.count()).select_from(Patient)),
        appointments_today=sum(by_status.values()),
        by_status=by_status,
        urgent_today=db.scalar(
            select(func.count()).select_from(Appointment).where(
                today, Appointment.priority == Priority.urgent, Appointment.status != AppointmentStatus.cancelled
            )
        ),
        busiest_doctor=busiest[0] if busiest else None,
    )
