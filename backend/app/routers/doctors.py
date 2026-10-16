from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.database import get_db
from app.models import Doctor
from app.schemas import DoctorCreate, DoctorOut, DoctorUpdate

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def get_doctor_or_404(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.get("", response_model=list[DoctorOut])
def list_doctors(active_only: bool = False, db: Session = Depends(get_db)):
    query = select(Doctor).order_by(Doctor.name)
    if active_only:
        query = query.where(Doctor.active.is_(True))
    return db.scalars(query).all()


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return get_doctor_or_404(db, doctor_id)


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    activity.log(db, "doctor", f"{doctor.name} ({doctor.specialty}) joined the clinic")
    db.commit()
    db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(db, doctor_id)
    changes = payload.model_dump(exclude_unset=True)
    if "active" in changes and changes["active"] != doctor.active:
        activity.log(db, "doctor", f"{doctor.name} is now {'on' if changes['active'] else 'off'} duty")
    for field, value in changes.items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(db, doctor_id)
    activity.log(db, "doctor", f"{doctor.name} was removed")
    db.delete(doctor)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
