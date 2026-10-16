from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import activity
from app.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, Patient, Priority
from app.schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.timeutils import as_naive_utc, day_range_utc, to_utc

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

INACTIVE = (AppointmentStatus.cancelled, AppointmentStatus.no_show)


def to_out(appt: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        start_time=appt.start_time,
        duration_min=appt.duration_min,
        reason=appt.reason,
        priority=appt.priority,
        status=appt.status,
        patient_name=appt.patient.full_name,
        doctor_name=appt.doctor.name,
        specialty=appt.doctor.specialty,
    )


def get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id, options=[joinedload(Appointment.patient), joinedload(Appointment.doctor)])
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def check_slot_free(db: Session, doctor_id: int, start, duration_min: int, ignore_id: int | None = None):
    """Raise 409 if the doctor already has an active appointment overlapping this slot."""
    start_utc = to_utc(start)
    end_utc = start_utc + timedelta(minutes=duration_min)
    # longest allowed appointment is 4h, so anything starting before that can't overlap
    query = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.status.not_in(INACTIVE),
        Appointment.start_time >= start_utc - timedelta(hours=4),
        Appointment.start_time < end_utc,
    )
    start, end = as_naive_utc(start_utc), as_naive_utc(end_utc)
    for other in db.scalars(query):
        if other.id == ignore_id:
            continue
        other_start = as_naive_utc(other.start_time)
        other_end = other_start + timedelta(minutes=other.duration_min)
        if start < other_end and other_start < end:
            raise HTTPException(status_code=409, detail="Doctor already has an appointment in this time slot")


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    day: date | None = None,
    doctor_id: int | None = None,
    status_filter: AppointmentStatus | None = None,
    priority: Priority | None = None,
    db: Session = Depends(get_db),
):
    query = (
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
        .order_by(Appointment.start_time)
    )
    if day:
        start, end = day_range_utc(day)
        query = query.where(Appointment.start_time >= start, Appointment.start_time < end)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    if priority:
        query = query.where(Appointment.priority == priority)
    return [to_out(a) for a in db.scalars(query).unique()]


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return to_out(get_appointment_or_404(db, appointment_id))


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.get(Patient, payload.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not doctor.active:
        raise HTTPException(status_code=400, detail="Doctor is not taking appointments")

    check_slot_free(db, payload.doctor_id, payload.start_time, payload.duration_min)
    appt = Appointment(**payload.model_dump(exclude={"start_time"}), start_time=to_utc(payload.start_time))
    db.add(appt)
    label = "Urgent appointment" if payload.priority == Priority.urgent else "Appointment"
    activity.log(db, "booking", f"{label} booked: {patient.full_name} with {doctor.name}")
    db.commit()
    return to_out(get_appointment_or_404(db, appt.id))


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = get_appointment_or_404(db, appointment_id)
    changes = payload.model_dump(exclude_unset=True)

    if "doctor_id" in changes and db.get(Doctor, changes["doctor_id"]) is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if "start_time" in changes:
        changes["start_time"] = to_utc(changes["start_time"])

    if {"doctor_id", "start_time", "duration_min"} & changes.keys():
        new_status = changes.get("status", appt.status)
        if new_status not in INACTIVE:
            check_slot_free(
                db,
                changes.get("doctor_id", appt.doctor_id),
                changes.get("start_time", appt.start_time),
                changes.get("duration_min", appt.duration_min),
                ignore_id=appt.id,
            )

    if "status" in changes and changes["status"] != appt.status:
        new_status = changes["status"].value.replace("_", " ")
        activity.log(db, "status", f"{appt.patient.full_name} marked {new_status} ({appt.doctor.name})")
    elif {"doctor_id", "start_time"} & changes.keys():
        activity.log(db, "booking", f"Appointment rescheduled for {appt.patient.full_name}")

    for field, value in changes.items():
        setattr(appt, field, value)
    db.commit()
    db.expire(appt)
    return to_out(get_appointment_or_404(db, appointment_id))


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = get_appointment_or_404(db, appointment_id)
    activity.log(db, "booking", f"Appointment deleted: {appt.patient.full_name} with {appt.doctor.name}")
    db.delete(appt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
