"""
Appointment Service
Validates bookings, prevents conflicts and duplicate slots, generates appointment IDs,
and manages appointment status lifecycles.
"""
import uuid
from datetime import datetime
from backend.models import Appointment, Doctor, User
from backend.database import db
from backend.calculator import is_day_available

def generate_appointment_id():
    """Generate professional, human-readable appointment ID e.g. APT-202509-4B8F"""
    now = datetime.now()
    short_uuid = uuid.uuid4().hex[:5].upper()
    return f"APT-{now.strftime('%Y%m')}-{short_uuid}"

def book_appointment(patient_id: int, doctor_id: int, appointment_date: str, appointment_time: str, reason: str = ""):
    """
    Validate and book an appointment.
    Checks:
    - Doctor exists and is active
    - Date format and validity (not past)
    - Weekday availability for doctor
    - Slot conflict (doctor already booked at that date & time)
    - Duplicate check (same patient already booked with this doctor on that date)
    """
    # 1. Validate Doctor
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return None, "Selected doctor does not exist."
    if doctor.status != "active":
        return None, f"Doctor {doctor.name} is currently not available for bookings ({doctor.status})."

    # 2. Validate Patient
    patient = db.session.get(User, patient_id)
    if not patient:
        return None, "Patient account not found."

    # 3. Validate Date
    try:
        booking_date = datetime.strptime(appointment_date.strip(), "%Y-%m-%d").date()
    except Exception:
        return None, "Invalid date format. Expected YYYY-MM-DD."

    today = datetime.now().date()
    if booking_date < today:
        return None, "Cannot book appointments for past dates."

    # 4. Validate Doctor weekday availability
    if not is_day_available(appointment_date, doctor.available_days):
        return None, f"{doctor.name} is only available on: {doctor.available_days}."

    # 5. Clean time string
    cleaned_time = appointment_time.strip()
    if not cleaned_time:
        return None, "Appointment time is required."

    # 6. Check slot conflict (Doctor already booked)
    existing_slot = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.appointment_time == cleaned_time,
        Appointment.status.in_(["confirmed", "pending"])
    ).first()

    if existing_slot:
        return None, f"The slot at {cleaned_time} on {appointment_date} is already booked. Please choose another time."

    # 7. Check duplicate booking for this patient with this doctor on same date
    duplicate_apt = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date,
        Appointment.status.in_(["confirmed", "pending"])
    ).first()

    if duplicate_apt:
        return None, f"You already have an appointment booked with {doctor.name} on {appointment_date} ({duplicate_apt.id})."

    # 8. Create appointment record
    appointment_id = generate_appointment_id()
    new_appointment = Appointment(
        id=appointment_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=cleaned_time,
        reason=reason.strip() if reason else "General Health Consultation",
        status="confirmed"
    )

    db.session.add(new_appointment)
    db.session.commit()
    return new_appointment, None

def get_user_appointments(user_id: int, role: str = "patient", status: str = None):
    """
    Get appointments for a user.
    If patient, return only their appointments.
    If staff or admin, return all appointments (with optional status filter).
    """
    query = Appointment.query
    if role == "patient":
        query = query.filter(Appointment.patient_id == user_id)
    if status:
        query = query.filter(Appointment.status == status)

    return query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

def get_appointment_by_id(appointment_id: str):
    """Retrieve single appointment by ID."""
    return db.session.get(Appointment, appointment_id)

def cancel_appointment(appointment_id: str, requesting_user_id: int, role: str):
    """
    Cancel an appointment.
    Patients can only cancel their own appointments. Staff/Admin can cancel any.
    """
    apt = db.session.get(Appointment, appointment_id)
    if not apt:
        return False, "Appointment not found."

    if role == "patient" and apt.patient_id != requesting_user_id:
        return False, "Unauthorized. You can only cancel your own appointments."

    if apt.status == "cancelled":
        return False, "This appointment is already cancelled."

    apt.status = "cancelled"
    db.session.commit()
    return True, None

def update_appointment_status(appointment_id: str, new_status: str):
    """Staff/Admin: update appointment status (e.g. pending, confirmed, completed, cancelled)."""
    valid_statuses = ["pending", "confirmed", "completed", "cancelled"]
    if new_status not in valid_statuses:
        return None, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

    apt = db.session.get(Appointment, appointment_id)
    if not apt:
        return None, "Appointment not found."

    apt.status = new_status
    db.session.commit()
    return apt, None
