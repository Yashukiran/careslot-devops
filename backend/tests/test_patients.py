def test_create_patient(client):
    res = client.post("/api/patients", json={"full_name": "Priya Iyer", "phone": "+91 99001 44556", "age": 28})
    assert res.status_code == 201
    assert res.json()["full_name"] == "Priya Iyer"


def test_duplicate_phone_rejected(client, patient):
    res = client.post("/api/patients", json={"full_name": "Someone Else", "phone": patient["phone"]})
    assert res.status_code == 409


def test_search_patients(client, patient):
    client.post("/api/patients", json={"full_name": "Kavya Reddy", "phone": "9740022334"})
    results = client.get("/api/patients", params={"q": "kavya"}).json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Kavya Reddy"


def test_update_and_delete_patient(client, patient):
    res = client.put(f"/api/patients/{patient['id']}", json={"notes": "allergic to penicillin"})
    assert res.json()["notes"] == "allergic to penicillin"
    assert client.delete(f"/api/patients/{patient['id']}").status_code == 204
    assert client.get(f"/api/patients/{patient['id']}").status_code == 404


def test_invalid_phone(client):
    res = client.post("/api/patients", json={"full_name": "Bad Phone", "phone": "abc"})
    assert res.status_code == 422
