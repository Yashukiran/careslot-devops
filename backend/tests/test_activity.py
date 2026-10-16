from tests.test_appointments import book, slot


def test_info_reports_version_and_database(client):
    res = client.get("/api/info")
    assert res.status_code == 200
    body = res.json()
    assert body["database"] == "ok"
    assert body["version"]


def test_booking_and_status_change_show_in_activity_feed(client, doctor, patient):
    appt = book(client, doctor, patient, slot(10)).json()
    client.put(f"/api/appointments/{appt['id']}", json={"status": "checked_in"})

    feed = client.get("/api/activity").json()
    messages = [a["message"] for a in feed]
    # newest first
    assert "checked in" in messages[0]
    assert any("booked" in m and patient["full_name"] in m for m in messages)


def test_activity_limit(client):
    for i in range(5):
        client.post("/api/doctors", json={"name": f"Dr. Test {i}", "specialty": "ENT"})
    assert len(client.get("/api/activity", params={"limit": 3}).json()) == 3


def test_urgent_priority(client, doctor, patient):
    book(client, doctor, patient, slot(9))
    urgent = book(client, doctor, patient, slot(11), priority="urgent").json()
    assert urgent["priority"] == "urgent"

    only_urgent = client.get("/api/appointments", params={"priority": "urgent"}).json()
    assert [a["id"] for a in only_urgent] == [urgent["id"]]
    assert client.get("/api/stats").json()["urgent_today"] == 1


def test_invalid_priority_rejected(client, doctor, patient):
    assert book(client, doctor, patient, slot(9), priority="asap").status_code == 422
