def test_create_and_get_doctor(client):
    res = client.post("/api/doctors", json={"name": "Dr. Vikram Mehta", "specialty": "Pediatrics", "room": "104"})
    assert res.status_code == 201
    doctor = res.json()
    assert doctor["id"] > 0
    assert doctor["active"] is True

    res = client.get(f"/api/doctors/{doctor['id']}")
    assert res.status_code == 200
    assert res.json()["specialty"] == "Pediatrics"


def test_list_doctors_active_only(client):
    client.post("/api/doctors", json={"name": "Dr. One", "specialty": "ENT"})
    client.post("/api/doctors", json={"name": "Dr. Two", "specialty": "ENT", "active": False})
    assert len(client.get("/api/doctors").json()) == 2
    active = client.get("/api/doctors", params={"active_only": True}).json()
    assert [d["name"] for d in active] == ["Dr. One"]


def test_update_doctor(client, doctor):
    res = client.put(f"/api/doctors/{doctor['id']}", json={"room": "305", "active": False})
    assert res.status_code == 200
    assert res.json()["room"] == "305"
    assert res.json()["active"] is False
    assert res.json()["name"] == doctor["name"]


def test_delete_doctor(client, doctor):
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404


def test_doctor_validation_error(client):
    res = client.post("/api/doctors", json={"name": "X", "specialty": ""})
    assert res.status_code == 422
