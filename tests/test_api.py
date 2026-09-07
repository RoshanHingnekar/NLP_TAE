"""
REST API Integration Tests
"""
import pytest
from backend.app import create_app
from backend.config import TestingConfig
from backend.database import db
from backend.models import Department, Doctor, FAQ, HospitalService

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed minimal test data
        dept = Department(
            id=1,
            name="Cardiology",
            description="Heart care",
            location="Wing A",
            opd_timing="09:00 - 17:00"
        )
        doc = Doctor(
            id=1,
            name="Dr. Test Specialist",
            department_id=1,
            specialization="Cardiologist",
            qualification="MD",
            experience="10 Years",
            available_days="Monday, Tuesday, Wednesday",
            start_time="09:00",
            end_time="17:00",
            consultation_fee=50.0,
            room_number="Room 101",
            status="active"
        )
        faq = FAQ(
            id=1,
            question="What are visiting hours?",
            answer="Visiting hours are 4 PM to 7 PM.",
            category="General"
        )
        srv = HospitalService(
            id=1,
            name="Emergency 24/7",
            description="Trauma care",
            location="Ground Floor",
            timing="24/7",
            contact="+1 555 019 9911"
        )
        db.session.add_all([dept, doc, faq, srv])
        db.session.commit()

        yield app.test_client()

        db.drop_all()

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"

def test_hospital_info(client):
    res = client.get("/api/hospital")
    assert res.status_code == 200
    data = res.get_json()
    assert data["is_demo"] is True
    assert "CareBridge" in data["name"]

def test_departments_api(client):
    res = client.get("/api/departments")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 1
    assert data[0]["name"] == "Cardiology"

def test_doctors_api(client):
    res = client.get("/api/doctors")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 1
    assert data[0]["name"] == "Dr. Test Specialist"

def test_faqs_api(client):
    res = client.get("/api/faqs")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 1
    assert "visiting hours" in data[0]["question"]

def test_services_api(client):
    res = client.get("/api/services")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) >= 1

def test_chat_api_normal(client):
    res = client.post("/api/chat", json={"message": "What are the OPD timings?"})
    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data
    assert data["safety_flag"] is False
    assert "session_id" in data

def test_chat_api_emergency(client):
    res = client.post("/api/chat", json={"message": "I have severe chest pain and cannot breathe"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["safety_flag"] is True
    assert "EMERGENCY NOTICE" in data["response"]
