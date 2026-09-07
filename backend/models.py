from datetime import datetime, timezone
import uuid
from backend.database import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="patient")  # patient, staff, admin
    created_at = db.Column(db.DateTime, default=utc_now)

    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")
    chat_sessions = db.relationship("ChatSession", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone or "",
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    opd_timing = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    doctors = db.relationship("Doctor", backref="department", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_doctors=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "opd_timing": self.opd_timing,
            "doctor_count": len(self.doctors) if self.doctors else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_doctors:
            data["doctors"] = [doc.to_dict() for doc in self.doctors]
        return data


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False, index=True)
    specialization = db.Column(db.String(150), nullable=False)
    qualification = db.Column(db.String(150), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    available_days = db.Column(db.String(200), nullable=False)  # e.g. "Monday, Tuesday, Wednesday, Friday"
    start_time = db.Column(db.String(20), nullable=False, default="09:00")
    end_time = db.Column(db.String(20), nullable=False, default="17:00")
    consultation_fee = db.Column(db.Float, nullable=False, default=50.0)
    room_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")  # active, on_leave, inactive
    created_at = db.Column(db.DateTime, default=utc_now)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        dept_name = self.department.name if self.department else ""
        return {
            "id": self.id,
            "name": self.name,
            "department_id": self.department_id,
            "department_name": dept_name,
            "specialization": self.specialization,
            "qualification": self.qualification,
            "experience": self.experience,
            "available_days": self.available_days,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "consultation_fee": float(self.consultation_fee),
            "room_number": self.room_number,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.String(50), primary_key=True)  # APT-2025-XXXX
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    appointment_date = db.Column(db.String(30), nullable=False, index=True)  # YYYY-MM-DD
    appointment_time = db.Column(db.String(20), nullable=False)  # HH:MM
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="confirmed")  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.name if self.patient else "Unknown Patient",
            "patient_email": self.patient.email if self.patient else "",
            "patient_phone": self.patient.phone if self.patient else "",
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.name if self.doctor else "Unknown Doctor",
            "department_name": self.doctor.department.name if (self.doctor and self.doctor.department) else "",
            "room_number": self.doctor.room_number if self.doctor else "",
            "consultation_fee": self.doctor.consultation_fee if self.doctor else 0.0,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "reason": self.reason or "General Consultation",
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class FAQ(db.Model):
    __tablename__ = "faqs"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="General")  # General, Appointments, Doctors, Departments, Billing, Insurance, Facilities
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class HospitalService(db.Model):
    __tablename__ = "hospital_services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    timing = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "timing": self.timing,
            "contact": self.contact,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def to_dict(self, include_messages=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }
        if include_messages:
            data["messages"] = [msg.to_dict() for msg in self.messages]
        return data


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # user, bot
    message = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(60), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    safety_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "sender": self.sender,
            "message": self.message,
            "intent": self.intent,
            "confidence": self.confidence,
            "safety_flag": bool(self.safety_flag),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
