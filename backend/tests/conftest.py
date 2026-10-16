import os

# never let the test run pick up the real database
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def doctor(client):
    res = client.post("/api/doctors", json={"name": "Dr. Ananya Rao", "specialty": "General Medicine", "room": "101"})
    return res.json()


@pytest.fixture()
def patient(client):
    res = client.post("/api/patients", json={"full_name": "Rahul Sharma", "phone": "+91 98450 11223", "age": 34})
    return res.json()
