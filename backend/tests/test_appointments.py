from datetime import datetime, timedelta

from app.timeutils import CLINIC_TZ


def slot(hour, minute=0, days=0):
    day = datetime.now(CLINIC_TZ).date() + timedelta(days=days)
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=CLINIC_TZ).isoformat()


def book(client, doctor, patient, start, **extra):
    body = {"patient_id": patient["id"], "doctor_id": doctor["id"], "start_time": start, **extra}
    return client.post("/api/appointments", json=body)


def test_book_appointment(client, doctor, patient):
    res = book(client, doctor, patient, slot(10), reason="Fever")
    assert res.status_code == 201
    appt = res.json()
    assert appt["status"] == "scheduled"
    assert appt["doctor_name"] == doctor["name"]
    assert appt["patient_name"] == patient["full_name"]


def test_double_booking_is_rejected(client, doctor, patient):
    assert book(client, doctor, patient, slot(10), duration_min=30).status_code == 201
    res = book(client, doctor, patient, slot(10, 15))
    assert res.status_code == 409
    # right after the first one ends is fine
    assert book(client, doctor, patient, slot(10, 30)).status_code == 201


def test_cancelled_slot_can_be_rebooked(client, doctor, patient):
    first = book(client, doctor, patient, slot(11)).json()
    client.put(f"/api/appointments/{first['id']}", json={"status": "cancelled"})
    assert book(client, doctor, patient, slot(11)).status_code == 201


def test_book_with_unknown_doctor(client, patient):
    res = book(client, {"id": 999}, patient, slot(9))
    assert res.status_code == 404


def test_inactive_doctor_cannot_take_bookings(client, doctor, patient):
    client.put(f"/api/doctors/{doctor['id']}", json={"active": False})
    assert book(client, doctor, patient, slot(9)).status_code == 400


def test_list_filters_by_day(client, doctor, patient):
    book(client, doctor, patient, slot(9))
    book(client, doctor, patient, slot(9, days=1))
    today = datetime.now(CLINIC_TZ).date().isoformat()
    assert len(client.get("/api/appointments").json()) == 2
    assert len(client.get("/api/appointments", params={"day": today}).json()) == 1


def test_update_status_and_delete(client, doctor, patient):
    appt = book(client, doctor, patient, slot(14)).json()
    res = client.put(f"/api/appointments/{appt['id']}", json={"status": "checked_in"})
    assert res.status_code == 200
    assert res.json()["status"] == "checked_in"

    assert client.delete(f"/api/appointments/{appt['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appt['id']}").status_code == 404


def test_stats(client, doctor, patient):
    book(client, doctor, patient, slot(9))
    second = book(client, doctor, patient, slot(12)).json()
    client.put(f"/api/appointments/{second['id']}", json={"status": "completed"})

    stats = client.get("/api/stats").json()
    assert stats["doctors"] == 1
    assert stats["patients"] == 1
    assert stats["appointments_today"] == 2
    assert stats["by_status"]["completed"] == 1
    assert stats["busiest_doctor"] == doctor["name"]
