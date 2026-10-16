from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import activity
from app.database import get_db
from app.models import Patient
from app.schemas import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["patients"])


def get_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def save(db: Session, patient: Patient) -> Patient:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A patient with this phone number already exists")
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(q: str | None = None, db: Session = Depends(get_db)):
    query = select(Patient).order_by(Patient.full_name)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Patient.full_name.ilike(like), Patient.phone.like(like)))
    return db.scalars(query).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return get_patient_or_404(db, patient_id)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    activity.log(db, "patient", f"New patient registered: {patient.full_name}")
    return save(db, patient)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = get_patient_or_404(db, patient_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    return save(db, patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = get_patient_or_404(db, patient_id)
    activity.log(db, "patient", f"Patient record removed: {patient.full_name}")
    db.delete(patient)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
