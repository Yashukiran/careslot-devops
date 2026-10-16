from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import AppointmentStatus, Priority


class DoctorBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    room: str = Field(default="", max_length=20)
    active: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    specialty: str | None = Field(default=None, min_length=2, max_length=80)
    room: str | None = Field(default=None, max_length=20)
    active: bool | None = None


class DoctorOut(DoctorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PatientBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=r"^\+?[0-9 ]{7,20}$")
    age: int | None = Field(default=None, ge=0, le=120)
    notes: str = ""


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9 ]{7,20}$")
    age: int | None = Field(default=None, ge=0, le=120)
    notes: str | None = None


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    start_time: datetime
    duration_min: int = Field(default=20, ge=5, le=240)
    reason: str = Field(default="", max_length=200)
    priority: Priority = Priority.routine


class AppointmentUpdate(BaseModel):
    doctor_id: int | None = None
    start_time: datetime | None = None
    duration_min: int | None = Field(default=None, ge=5, le=240)
    reason: str | None = Field(default=None, max_length=200)
    priority: Priority | None = None
    status: AppointmentStatus | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    doctor_id: int
    start_time: datetime
    duration_min: int
    reason: str
    priority: Priority
    status: AppointmentStatus
    patient_name: str
    doctor_name: str
    specialty: str


class Stats(BaseModel):
    doctors: int
    patients: int
    appointments_today: int
    by_status: dict[str, int]
    urgent_today: int
    busiest_doctor: str | None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    message: str
    created_at: datetime


class Info(BaseModel):
    service: str
    version: str
    environment: str
    database: str
