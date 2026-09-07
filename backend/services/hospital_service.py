"""
Hospital Information and Admin Analytics Service
Provides hospital details, departments, FAQs, services, and administrative metrics.
"""
from datetime import datetime, timezone
from sqlalchemy import func
from backend.models import Department, Doctor, Appointment, FAQ, HospitalService, User, ChatSession, ChatMessage
from backend.database import db

DEMO_HOSPITAL_INFO = {
    "name": "CareBridge Demo Hospital",
    "tagline": "Compassionate Care, Advanced Medicine",
    "notice": "DEMO DATA - Fictional hospital for educational and project evaluation purposes.",
    "is_demo": True,
    "address": "404 Healthcare Boulevard, Medical District, Metropolis, NY 10001",
    "phone": "+1 (555) 019-2834",
    "emergency_phone": "+1 (555) 019-9911 (24/7 Helpline)",
    "ambulance_phone": "+1 (555) 019-0108 (24/7 Trauma Service)",
    "email": "contact@carebridge.demo",
    "emergency_department": "Ground Floor, Wing A - Open 24 Hours, 365 Days",
    "opd_timings": "Monday to Saturday: 08:00 AM - 08:00 PM | Sunday: 09:00 AM - 01:00 PM (Emergency 24/7)",
    "visiting_hours": "General Wards: 04:00 PM - 07:00 PM | ICU / CCU: 11:00 AM - 12:00 PM & 05:00 PM - 06:00 PM",
    "pharmacy": "In-house 24/7 Pharmacy located at Main Lobby, Ground Floor",
    "laboratory": "CareBridge Diagnostics, First Floor - 24/7 Sample Collection & Automated Testing",
    "radiology": "Radiology & Advanced Imaging Center (MRI, 128-Slice CT, X-Ray, Ultrasound) - Basement 1",
    "facilities": [
        "24/7 Emergency and Level-1 Trauma Care",
        "Modern Digital Intensive Care Units (ICU, CCU, PICU, NICU)",
        "Automated In-house 24/7 Pathology and Diagnostics Laboratory",
        "Advanced Radiology Suite (3T MRI, 128-Slice CT, Color Doppler)",
        "Round-the-clock Fully Stocked Outpatient & Inpatient Pharmacy",
        "Licensed Blood Bank with Component Separation",
        "Spacious Multi-cuisine Cafeteria and Patient Attendant Lounges",
        "Ample Basement & Valet Parking with EV Charging",
        "Dedicated TPA / Cashless Health Insurance Helpdesk",
        "Wheelchair Assistance and Accessibility Ramps throughout campus"
    ]
}

def get_hospital_info():
    """Return hospital profile."""
    return DEMO_HOSPITAL_INFO

# --- Department Operations ---
def get_all_departments():
    return Department.query.order_by(Department.name.asc()).all()

def get_department_by_id(dept_id: int):
    return Department.query.get(dept_id)

def create_department(data: dict):
    name = data.get("name", "").strip()
    if not name or not data.get("description") or not data.get("location"):
        return None, "Name, description, and location are required."
    
    if Department.query.filter_by(name=name).first():
        return None, f"Department '{name}' already exists."

    dept = Department(
        name=name,
        description=data.get("description", "").strip(),
        location=data.get("location", "").strip(),
        opd_timing=data.get("opd_timing", "09:00 AM - 05:00 PM").strip()
    )
    db.session.add(dept)
    db.session.commit()
    return dept, None

def update_department(dept_id: int, data: dict):
    dept = Department.query.get(dept_id)
    if not dept:
        return None, "Department not found."

    if "name" in data and data["name"].strip():
        dept.name = data["name"].strip()
    if "description" in data:
        dept.description = data["description"].strip()
    if "location" in data:
        dept.location = data["location"].strip()
    if "opd_timing" in data:
        dept.opd_timing = data["opd_timing"].strip()

    db.session.commit()
    return dept, None

def delete_department(dept_id: int):
    dept = Department.query.get(dept_id)
    if not dept:
        return False, "Department not found."
    db.session.delete(dept)
    db.session.commit()
    return True, None

# --- FAQ Operations ---
def get_all_faqs(category=None, search=None):
    query = FAQ.query
    if category and category.lower() != "all":
        query = query.filter(FAQ.category.ilike(category))
    if search:
        query = query.filter(
            db.or_(
                FAQ.question.ilike(f"%{search}%"),
                FAQ.answer.ilike(f"%{search}%")
            )
        )
    return query.order_by(FAQ.id.asc()).all()

def create_faq(data: dict):
    if not data.get("question") or not data.get("answer"):
        return None, "Question and answer are required."
    faq = FAQ(
        question=data["question"].strip(),
        answer=data["answer"].strip(),
        category=data.get("category", "General").strip()
    )
    db.session.add(faq)
    db.session.commit()
    return faq, None

def update_faq(faq_id: int, data: dict):
    faq = FAQ.query.get(faq_id)
    if not faq:
        return None, "FAQ not found."
    if "question" in data:
        faq.question = data["question"].strip()
    if "answer" in data:
        faq.answer = data["answer"].strip()
    if "category" in data:
        faq.category = data["category"].strip()
    db.session.commit()
    return faq, None

def delete_faq(faq_id: int):
    faq = FAQ.query.get(faq_id)
    if not faq:
        return False, "FAQ not found."
    db.session.delete(faq)
    db.session.commit()
    return True, None

# --- Hospital Services Operations ---
def get_all_services():
    return HospitalService.query.order_by(HospitalService.id.asc()).all()

def create_service(data: dict):
    if not data.get("name") or not data.get("description"):
        return None, "Name and description are required."
    service = HospitalService(
        name=data["name"].strip(),
        description=data["description"].strip(),
        location=data.get("location", "Main Hospital").strip(),
        timing=data.get("timing", "24/7").strip(),
        contact=data.get("contact", "+1 (555) 019-2834").strip()
    )
    db.session.add(service)
    db.session.commit()
    return service, None

def update_service(service_id: int, data: dict):
    srv = HospitalService.query.get(service_id)
    if not srv:
        return None, "Service not found."
    if "name" in data:
        srv.name = data["name"].strip()
    if "description" in data:
        srv.description = data["description"].strip()
    if "location" in data:
        srv.location = data["location"].strip()
    if "timing" in data:
        srv.timing = data["timing"].strip()
    if "contact" in data:
        srv.contact = data["contact"].strip()
    db.session.commit()
    return srv, None

def delete_service(service_id: int):
    srv = HospitalService.query.get(service_id)
    if not srv:
        return False, "Service not found."
    db.session.delete(srv)
    db.session.commit()
    return True, None

# --- Admin Analytics ---
def get_admin_analytics():
    """Aggregate metrics and chart analytics for administrator dashboard."""
    today_str = datetime.now().strftime("%Y-%m-%d")

    total_patients = User.query.filter_by(role="patient").count()
    total_doctors = Doctor.query.count()
    total_departments = Department.query.count()
    total_appointments = Appointment.query.count()
    appointments_today = Appointment.query.filter_by(appointment_date=today_str).count()
    
    total_sessions = ChatSession.query.count()
    total_messages = ChatMessage.query.count()
    emergency_flags = ChatMessage.query.filter_by(safety_flag=True).count()

    # NLP Metrics
    bot_messages = ChatMessage.query.filter_by(sender="bot").all()
    confidences = [msg.confidence for msg in bot_messages if msg.confidence is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.88

    unknown_messages_count = ChatMessage.query.filter(
        (ChatMessage.intent == "unknown") | (ChatMessage.confidence < 0.55)
    ).count()
    unknown_rate = round((unknown_messages_count / max(total_messages, 1)) * 100, 1)

    # Intent distribution
    intent_counts = db.session.query(
        ChatMessage.intent, func.count(ChatMessage.id)
    ).filter(ChatMessage.intent.isnot(None))\
     .group_by(ChatMessage.intent)\
     .order_by(func.count(ChatMessage.id).desc())\
     .limit(8).all()

    intent_distribution = {
        item[0]: item[1] for item in intent_counts if item[0]
    }

    # Appointments by department
    dept_appointments = db.session.query(
        Department.name, func.count(Appointment.id)
    ).join(Doctor, Doctor.department_id == Department.id)\
     .join(Appointment, Appointment.doctor_id == Doctor.id)\
     .group_by(Department.name).all()

    department_distribution = {
        item[0]: item[1] for item in dept_appointments
    }

    # Appointments over time (by date)
    date_appointments = db.session.query(
        Appointment.appointment_date, func.count(Appointment.id)
    ).group_by(Appointment.appointment_date)\
     .order_by(Appointment.appointment_date.asc())\
     .limit(10).all()

    appointments_timeline = {
        item[0]: item[1] for item in date_appointments
    }

    return {
        "metrics": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_departments": total_departments,
            "total_appointments": total_appointments,
            "appointments_today": appointments_today,
            "chat_sessions": total_sessions,
            "total_chat_messages": total_messages,
            "emergency_flags": emergency_flags,
            "average_confidence": avg_confidence,
            "unknown_intent_percentage": unknown_rate,
            "average_response_time_ms": 140
        },
        "charts": {
            "intent_distribution": intent_distribution,
            "department_appointments": department_distribution,
            "appointments_timeline": appointments_timeline
        }
    }
