"""
Appointment Booking and Lifecycle Unit Tests
"""
from datetime import datetime, timedelta
import pytest
from backend.app import create_app
from backend.config import TestingConfig
from backend.database import db
from backend.models import User, Department, Doctor, Appointment
from backend.services.auth_service import hash_password

@pytest.fixture
def client_and_data():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        dept = Department(id=1, name="Cardiology", description="Heart", location="Wing A", opd_timing="09:00-17:00")
        doc = Doctor(
            id=1,
            name="Dr. Sarah Connor",
            department_id=1,
            specialization="Cardiologist",
            qualification="MD",
            experience="10 Years",
            available_days="Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday",
            start_time="09:00",
            end_time="17:00",
            consultation_fee=60.0,
            room_number="Room 101",
            status="active"
        )
        patient = User(
            id=1,
            name="John Patient",
            email="john@test.com",
            password_hash=hash_password("Pass123"),
            role="patient"
        )
        db.session.add_all([dept, doc, patient])
        db.session.commit()

        client = app.test_client()

        # Login to get token
        res = client.post("/api/auth/login", json={"email": "john@test.com", "password": "Pass123"})
        token = res.get_json()["token"]

        yield client, token, doc.id

        db.drop_all()

def test_valid_booking(client_and_data):
    client, token, doc_id = client_and_data
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    res = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": doc_id,
            "appointment_date": tomorrow_str,
            "appointment_time": "10:00",
            "reason": "Routine Checkup"
        }
    )
    assert res.status_code == 201
    data = res.get_json()
    assert "appointment" in data
    assert data["appointment"]["id"].startswith("APT-")
    assert data["appointment"]["status"] == "confirmed"

def test_invalid_doctor(client_and_data):
    client, token, _ = client_and_data
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    res = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": 9999,
            "appointment_date": tomorrow_str,
            "appointment_time": "10:00"
        }
    )
    assert res.status_code == 400
    assert "Selected doctor does not exist" in res.get_json()["message"]

def test_past_date_booking(client_and_data):
    client, token, doc_id = client_and_data
    past_date_str = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    res = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": doc_id,
            "appointment_date": past_date_str,
            "appointment_time": "10:00"
        }
    )
    assert res.status_code == 400
    assert "past dates" in res.get_json()["message"]

def test_duplicate_slot_conflict(client_and_data):
    client, token, doc_id = client_and_data
    future_date_str = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    # First booking succeeds
    res1 = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": doc_id,
            "appointment_date": future_date_str,
            "appointment_time": "11:00",
            "reason": "First consultation"
        }
    )
    assert res1.status_code == 201

    # Second booking for same doctor, date and time -> rejected
    res2 = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": doc_id,
            "appointment_date": future_date_str,
            "appointment_time": "11:00",
            "reason": "Second consultation attempt"
        }
    )
    assert res2.status_code == 400

def test_cancel_appointment(client_and_data):
    client, token, doc_id = client_and_data
    future_date_str = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")

    # Book
    res = client.post("/api/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "doctor_id": doc_id,
            "appointment_date": future_date_str,
            "appointment_time": "14:00"
        }
    )
    apt_id = res.get_json()["appointment"]["id"]

    # Cancel
    cancel_res = client.delete(f"/api/appointments/{apt_id}", headers={"Authorization": f"Bearer {token}"})
    assert cancel_res.status_code == 200

    # Verify status changed to cancelled
    get_res = client.get(f"/api/appointments/{apt_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 200
    assert get_res.get_json()["status"] == "cancelled"
