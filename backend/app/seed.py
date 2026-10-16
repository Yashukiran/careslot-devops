"""Adds a few doctors, patients and today's appointments so the dashboard isn't empty on a fresh install."""
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Appointment, AppointmentStatus, Doctor, Patient
from app.timeutils import CLINIC_TZ, to_utc, today_local

DOCTORS = [
    ("Dr. Ananya Rao", "General Medicine", "101"),
    ("Dr. Vikram Mehta", "Pediatrics", "104"),
    ("Dr. Sara Thomas", "Dermatology", "202"),
    ("Dr. Arjun Nair", "Orthopedics", "205"),
]

PATIENTS = [
    ("Rahul Sharma", "+91 98450 11223", 34),
    ("Priya Iyer", "+91 99001 44556", 28),
    ("Mohammed Faiz", "+91 90080 77889", 52),
    ("Kavya Reddy", "+91 97400 22334", 7),
    ("Neha Gupta", "+91 98860 55667", 41),
    ("Suresh Kumar", "+91 96320 88990", 63),
]

# (patient index, doctor index, hour, minute, reason, status)
TODAY = [
    (0, 0, 9, 30, "Fever and body ache", AppointmentStatus.completed),
    (3, 1, 10, 0, "Vaccination", AppointmentStatus.checked_in),
    (1, 2, 11, 0, "Skin rash follow-up", AppointmentStatus.scheduled),
    (5, 3, 12, 0, "Knee pain", AppointmentStatus.scheduled),
    (2, 0, 15, 30, "BP review", AppointmentStatus.scheduled),
    (4, 2, 16, 0, "Acne consultation", AppointmentStatus.cancelled),
]


def seed() -> bool:
    db = SessionLocal()
    try:
        if db.scalar(select(Doctor.id).limit(1)) is not None:
            return False
        doctors = [Doctor(name=n, specialty=s, room=r) for n, s, r in DOCTORS]
        patients = [Patient(full_name=n, phone=p, age=a) for n, p, a in PATIENTS]
        db.add_all(doctors + patients)
        db.flush()

        day = today_local()
        for p, d, hh, mm, reason, status in TODAY:
            start = datetime.combine(day, time(hh, mm), tzinfo=CLINIC_TZ)
            db.add(Appointment(patient_id=patients[p].id, doctor_id=doctors[d].id, start_time=to_utc(start),
                               duration_min=20, reason=reason, status=status))
        tomorrow = datetime.combine(day + timedelta(days=1), time(10, 30), tzinfo=CLINIC_TZ)
        db.add(Appointment(patient_id=patients[0].id, doctor_id=doctors[0].id, start_time=to_utc(tomorrow),
                           reason="Report review"))
        db.commit()
        return True
    except IntegrityError:
        # another replica seeded at the same moment
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("seeded" if seed() else "database already has data, skipping")
