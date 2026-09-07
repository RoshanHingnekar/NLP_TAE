"""
Authentication and Role Authorization Unit Tests
"""
import pytest
from backend.app import create_app
from backend.config import TestingConfig
from backend.database import db
from backend.models import User
from backend.services.auth_service import hash_password

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed test admin & patient
        admin_u = User(
            name="Admin Test",
            email="admin@test.com",
            password_hash=hash_password("AdminPass123"),
            role="admin"
        )
        patient_u = User(
            name="Patient Test",
            email="patient@test.com",
            password_hash=hash_password("PatientPass123"),
            role="patient"
        )
        db.session.add_all([admin_u, patient_u])
        db.session.commit()

        yield app.test_client()
        db.drop_all()

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "name": "New Person",
        "email": "new.person@test.com",
        "password": "SecretPassword123",
        "phone": "+1 555 123 4567"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "token" in data
    assert data["user"]["email"] == "new.person@test.com"

def test_register_duplicate_email(client):
    res = client.post("/api/auth/register", json={
        "name": "Duplicate",
        "email": "patient@test.com",
        "password": "Password123"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert "already exists" in data["message"]

def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "patient@test.com",
        "password": "PatientPass123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data
    assert data["user"]["email"] == "patient@test.com"

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "patient@test.com",
        "password": "WrongPassword"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert "Invalid" in data["message"]

def test_protected_me_endpoint(client):
    # Without token -> 401
    res = client.get("/api/auth/me")
    assert res.status_code == 401

    # Login to obtain token
    login_res = client.post("/api/auth/login", json={
        "email": "patient@test.com",
        "password": "PatientPass123"
    })
    token = login_res.get_json()["token"]

    # With token -> 200
    auth_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200
    assert auth_res.get_json()["user"]["name"] == "Patient Test"

def test_role_authorization(client):
    # Patient token
    login_patient = client.post("/api/auth/login", json={
        "email": "patient@test.com",
        "password": "PatientPass123"
    })
    patient_token = login_patient.get_json()["token"]

    # Patient accessing admin endpoint -> 403 Forbidden
    res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 403

    # Admin token
    login_admin = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass123"
    })
    admin_token = login_admin.get_json()["token"]

    # Admin accessing admin endpoint -> 200 OK
    admin_res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
