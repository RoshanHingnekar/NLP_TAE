"""
Doctor Service
Handles doctor queries, filtering, availability slots, and admin CRUD.
"""
from backend.models import Doctor, Department, Appointment
from backend.database import db
from backend.calculator import generate_slots, is_day_available

def get_all_doctors(department_id=None, specialization=None, search=None, status="active"):
    """Fetch doctors matching criteria."""
    query = Doctor.query
    if status:
        query = query.filter(Doctor.status == status)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if search:
        query = query.filter(
            db.or_(
                Doctor.name.ilike(f"%{search}%"),
                Doctor.specialization.ilike(f"%{search}%"),
                Doctor.qualification.ilike(f"%{search}%")
            )
        )
    return query.order_by(Doctor.name.asc()).all()

def get_doctor_by_id(doctor_id: int):
    """Retrieve single doctor."""
    return Doctor.query.get(doctor_id)

def get_doctor_availability(doctor_id: int, target_date: str):
    """
    Calculate available time slots for a doctor on a specific date.
    Validates weekday availability and checks against existing appointments.
    """
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return None, "Doctor not found."

    if doctor.status != "active":
        return {
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "target_date": target_date,
            "is_available_day": False,
            "message": f"{doctor.name} is currently not available ({doctor.status}).",
            "available_slots": [],
            "booked_slots": []
        }, None

    # Check day of week
    is_avail = is_day_available(target_date, doctor.available_days)
    if not is_avail:
        return {
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "target_date": target_date,
            "is_available_day": False,
            "message": f"{doctor.name} does not consult on this day. Available days: {doctor.available_days}",
            "available_slots": [],
            "booked_slots": []
        }, None

    # Generate all candidate slots
    all_slots = generate_slots(doctor.start_time, doctor.end_time, interval_minutes=30)

    # Query already booked slots for this doctor on target_date
    booked_apts = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == target_date,
        Appointment.status.in_(["confirmed", "pending"])
    ).all()
    booked_times = set(apt.appointment_time for apt in booked_apts)

    available_slots = [slot for slot in all_slots if slot not in booked_times]

    return {
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "department": doctor.department.name if doctor.department else "",
        "target_date": target_date,
        "is_available_day": True,
        "working_hours": f"{doctor.start_time} - {doctor.end_time}",
        "room_number": doctor.room_number,
        "consultation_fee": doctor.consultation_fee,
        "all_slots": all_slots,
        "available_slots": available_slots,
        "booked_slots": list(booked_times)
    }, None

def create_doctor(data):
    """Admin: create new doctor record."""
    required = ["name", "department_id", "specialization", "qualification", "experience", "available_days"]
    for field in required:
        if field not in data or not str(data[field]).strip():
            return None, f"Field '{field}' is required."

    # Validate department exists
    dept = Department.query.get(data["department_id"])
    if not dept:
        return None, "Selected department does not exist."

    doctor = Doctor(
        name=data["name"].strip(),
        department_id=int(data["department_id"]),
        specialization=data["specialization"].strip(),
        qualification=data["qualification"].strip(),
        experience=data["experience"].strip(),
        available_days=data["available_days"].strip(),
        start_time=data.get("start_time", "09:00").strip(),
        end_time=data.get("end_time", "17:00").strip(),
        consultation_fee=float(data.get("consultation_fee", 50.0)),
        room_number=data.get("room_number", "Room 101").strip(),
        status=data.get("status", "active").strip()
    )
    db.session.add(doctor)
    db.session.commit()
    return doctor, None

def update_doctor(doctor_id: int, data: dict):
    """Admin: update existing doctor."""
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return None, "Doctor not found."

    if "name" in data:
        doctor.name = data["name"].strip()
    if "department_id" in data:
        dept = Department.query.get(data["department_id"])
        if not dept:
            return None, "Invalid department ID."
        doctor.department_id = int(data["department_id"])
    if "specialization" in data:
        doctor.specialization = data["specialization"].strip()
    if "qualification" in data:
        doctor.qualification = data["qualification"].strip()
    if "experience" in data:
        doctor.experience = data["experience"].strip()
    if "available_days" in data:
        doctor.available_days = data["available_days"].strip()
    if "start_time" in data:
        doctor.start_time = data["start_time"].strip()
    if "end_time" in data:
        doctor.end_time = data["end_time"].strip()
    if "consultation_fee" in data:
        doctor.consultation_fee = float(data["consultation_fee"])
    if "room_number" in data:
        doctor.room_number = data["room_number"].strip()
    if "status" in data:
        doctor.status = data["status"].strip()

    db.session.commit()
    return doctor, None

def delete_doctor(doctor_id: int):
    """Admin: delete doctor record."""
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return False, "Doctor not found."
    db.session.delete(doctor)
    db.session.commit()
    return True, None
