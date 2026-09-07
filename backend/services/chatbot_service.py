"""
Chatbot Service
Orchestrates the entire NLP pipeline, database retrieval, multi-turn dialogue context,
and database persistence of chat history.
"""
import uuid
from datetime import datetime, timezone
from flask import current_app

from backend.models import ChatSession, ChatMessage, Department, Doctor, Appointment, FAQ, HospitalService
from backend.database import db
from backend.nlp.chatbot import nlp_engine
from backend.nlp.safety import (
    detect_emergency, get_emergency_response, get_safe_symptom_guidance,
    GENERAL_MEDICAL_DISCLAIMER
)
from backend.services.hospital_service import DEMO_HOSPITAL_INFO

def get_or_create_session(session_id=None, user_id=None):
    """Retrieve existing chat session or create a new one."""
    if session_id:
        session = ChatSession.query.get(session_id)
        if session:
            if user_id and not session.user_id:
                session.user_id = user_id
                db.session.commit()
            return session

    # Generate new session
    new_id = session_id or str(uuid.uuid4())
    session = ChatSession(id=new_id, user_id=user_id)
    db.session.add(session)
    db.session.commit()
    return session

def process_chat_message(message_text: str, session_id: str = None, user=None):
    """
    Core pipeline:
    USER MESSAGE -> NORMALIZATION -> INTENT -> ENTITIES -> CONTEXT -> DB RETRIEVAL -> SAFETY -> RESPONSE -> PERSISTENCE
    """
    user_id = user.id if user else None
    session = get_or_create_session(session_id, user_id)
    active_session_id = session.id

    # 1. Medical Safety / Emergency Priority Check
    if detect_emergency(message_text):
        emergency_resp = get_emergency_response()
        # Save messages to DB
        _save_chat_turn(active_session_id, message_text, emergency_resp, intent="emergency", confidence=1.0, safety_flag=True)
        return {
            "response": emergency_resp,
            "intent": "emergency",
            "confidence": 1.0,
            "entities": {},
            "safety_flag": True,
            "session_id": active_session_id
        }

    # 2. Extract Entities
    entities = nlp_engine.extract_entities(message_text)

    # 3. Predict Intent & Confidence
    intent, confidence = nlp_engine.predict_intent(message_text)

    # 4. Multi-turn Context Management
    context = nlp_engine.get_context(active_session_id)
    nlp_engine.update_context(active_session_id, entities, intent)

    # Threshold check
    threshold = current_app.config.get("NLP_CONFIDENCE_THRESHOLD", 0.55)
    
    # 5. Route Intent & Retrieve Knowledge from Database
    safety_flag = False

    # Check multi-turn appointment follow-up
    if context.get("step") == "awaiting_booking_details" and intent not in ["emergency", "greeting", "goodbye"]:
        response_text = _handle_booking_flow(message_text, entities, context, active_session_id)
    elif confidence < threshold and intent not in ["greeting", "goodbye", "thanks", "emergency"]:
        response_text = (
            "I'm not completely sure I understood your question. I can help with doctors, "
            "departments, appointments, hospital services, timings and general health information. "
            "Could you please rephrase your question?"
        )
        intent = "unknown"
    else:
        response_text, safety_flag = _generate_response(intent, entities, message_text, active_session_id, user)

    # 6. Save Turn to Database
    _save_chat_turn(active_session_id, message_text, response_text, intent, confidence, safety_flag)

    return {
        "response": response_text,
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "safety_flag": safety_flag,
        "session_id": active_session_id
    }

def _generate_response(intent: str, entities: dict, raw_text: str, session_id: str, user=None):
    """Generate dynamic response based on classified intent and real database contents."""
    safety_flag = False

    if intent == "greeting":
        user_name = f", {user.name}" if user else ""
        return (
            f"Hello{user_name}! I'm your CareBridge Hospital Assistant. "
            "I can help you search doctors, check OPD timings, book or check appointments, "
            "explore departments, and answer hospital inquiries. How can I assist you today?"
        ), False

    elif intent == "goodbye":
        return (
            "Thank you for reaching out to CareBridge Hospital Assistant. "
            "Take care and have a healthy day ahead! Feel free to ask whenever you need assistance."
        ), False

    elif intent == "thanks":
        return (
            "You are very welcome! If you have any other questions about appointments, "
            "doctors, or hospital services, I am always here to help."
        ), False

    elif intent == "hospital_information":
        return (
            f"{DEMO_HOSPITAL_INFO['name']} is a modern multi-specialty healthcare facility dedicated to "
            "excellence in patient care and clinical services.\n"
            f"• Address: {DEMO_HOSPITAL_INFO['address']}\n"
            f"• Emergency: {DEMO_HOSPITAL_INFO['emergency_phone']}\n"
            f"• General Enquiries: {DEMO_HOSPITAL_INFO['phone']}\n"
            "We offer 13+ specialized departments and 24/7 critical care."
        ), False

    elif intent == "hospital_location":
        return (
            f"CareBridge Hospital is located at:\n"
            f"{DEMO_HOSPITAL_INFO['address']}.\n"
            "• Landmarks: Situated opposite Metro Central Station, Exit Gate 3.\n"
            "• Parking: Dedicated 3-level visitor parking with 24/7 valet service."
        ), False

    elif intent == "contact_information":
        return (
            "Here are the important contact numbers for CareBridge Hospital:\n"
            f"• 24/7 Emergency Casualty: {DEMO_HOSPITAL_INFO['emergency_phone']}\n"
            f"• 24/7 Ambulance Hotline: {DEMO_HOSPITAL_INFO['ambulance_phone']}\n"
            f"• Appointments & General Desk: {DEMO_HOSPITAL_INFO['phone']}\n"
            f"• Email Support: {DEMO_HOSPITAL_INFO['email']}"
        ), False

    elif intent == "opd_timings":
        return (
            f"Our Outpatient Department (OPD) operates as follows:\n"
            f"• {DEMO_HOSPITAL_INFO['opd_timings']}\n"
            "• Morning Shift: 08:00 AM - 01:00 PM\n"
            "• Evening Shift: 02:00 PM - 08:00 PM\n"
            "Emergency Casualty is open 24/7 round the clock."
        ), False

    elif intent == "visiting_hours":
        return (
            f"Visitor timings for admitted patients:\n"
            f"• {DEMO_HOSPITAL_INFO['visiting_hours']}\n"
            "Please note: Only one visitor pass is permitted in ICU/CCU rooms at a time to ensure patient hygiene."
        ), False

    elif intent == "pharmacy_information":
        return (
            f"{DEMO_HOSPITAL_INFO['pharmacy']}.\n"
            "We stock all essential prescription medications, surgical supplies, and pediatric formulations. "
            "Inpatient bedside delivery is also provided."
        ), False

    elif intent == "laboratory_information":
        return (
            f"{DEMO_HOSPITAL_INFO['laboratory']}.\n"
            "We offer routine blood work (CBC, Lipid, LFT/KFT), pathology, microbiology, and molecular tests. "
            "Digital lab reports are accessible online within 4-6 hours for most routine tests."
        ), False

    elif intent == "radiology_information":
        return (
            f"{DEMO_HOSPITAL_INFO['radiology']}.\n"
            "Services include 3.0 Tesla MRI, 128-Slice Low-Dose CT, Digital X-Ray, Color Doppler 4D Ultrasound, "
            "and Bone Densitometry (DEXA). Emergency scans operate 24/7."
        ), False

    elif intent == "facilities":
        fac_list = "\n".join([f"• {fac}" for fac in DEMO_HOSPITAL_INFO["facilities"][:6]])
        return (
            f"CareBridge Hospital offers first-class healthcare amenities:\n{fac_list}\n"
            "Would you like details on any specific facility?"
        ), False

    elif intent == "insurance":
        return (
            "We have tie-ups with 30+ leading health insurance providers and TPAs (e.g., Star Health, "
            "HDFC ERGO, Max Bupa, ICICI Lombard, Medi Assist, Paramount TPA).\n"
            "Our Cashless TPA Helpdesk is located on the Ground Floor next to Admission Desk, open 24/7."
        ), False

    elif intent == "billing":
        return (
            "CareBridge Hospital provides transparent, itemized billing.\n"
            "• Payment Methods: Credit/Debit Cards, UPI, Net Banking, and Cash.\n"
            "• Helpdesk: Billing & Discharge counter operates in the Main Atrium from 07:00 AM to 10:00 PM.\n"
            "You can also pay and download receipts via your Patient Dashboard."
        ), False

    elif intent == "health_check":
        return (
            "We offer comprehensive Preventive Health Screening packages:\n"
            "1. CareBridge Comprehensive Master Health Check ($199)\n"
            "2. Executive Cardiac Care Package ($249)\n"
            "3. Senior Citizen Wellness Profile ($179)\n"
            "4. Women's Special Health Package ($189)\n"
            "All packages include physician review and nutritional consultation."
        ), False

    elif intent == "department_information":
        dept_name = entities.get("department")
        if dept_name:
            dept = Department.query.filter(Department.name.ilike(f"%{dept_name}%")).first()
            if dept:
                doc_count = len(dept.doctors)
                return (
                    f"Department of {dept.name}:\n"
                    f"• Overview: {dept.description}\n"
                    f"• Location: {dept.location}\n"
                    f"• OPD Timings: {dept.opd_timing}\n"
                    f"• Active Doctors: {doc_count}\n"
                    "Would you like to see available doctors or book a consultation in this department?"
                ), False

        depts = Department.query.all()
        dept_names = [d.name for d in depts]
        return (
            f"CareBridge Hospital features {len(dept_names)} specialized clinical departments:\n"
            f"{', '.join(dept_names)}.\n\n"
            "Which department would you like to know more about or see doctors for?"
        ), False

    elif intent == "doctor_information":
        # Search by specific doctor entity if captured
        if "doctor" in entities:
            doc_query = entities["doctor"].replace("Dr.", "").strip()
            doctor = Doctor.query.filter(Doctor.name.ilike(f"%{doc_query}%")).first()
            if doctor:
                return (
                    f"Doctor Profile: {doctor.name}\n"
                    f"• Specialization: {doctor.specialization}\n"
                    f"• Department: {doctor.department.name if doctor.department else 'General'}\n"
                    f"• Qualifications: {doctor.qualification} ({doctor.experience} experience)\n"
                    f"• Consulting Hours: {doctor.available_days} ({doctor.start_time} - {doctor.end_time})\n"
                    f"• Consultation Fee: ${doctor.consultation_fee:.2f} | Room: {doctor.room_number}\n"
                    f"Would you like to book an appointment with {doctor.name}?"
                ), False

        # If department is specified
        if "department" in entities:
            dept = Department.query.filter(Department.name.ilike(f"%{entities['department']}%")).first()
            if dept and dept.doctors:
                doc_lines = [f"• {d.name} ({d.specialization}) - {d.available_days}" for d in dept.doctors]
                return (
                    f"Doctors in {dept.name}:\n" + "\n".join(doc_lines) +
                    "\n\nWould you like to book an appointment with any of these specialists?"
                ), False

        # General doctors listing
        sample_doctors = Doctor.query.limit(4).all()
        doc_lines = [f"• {d.name} ({d.department.name} - {d.specialization})" for d in sample_doctors]
        return (
            "We have experienced medical specialists across all divisions:\n" +
            "\n".join(doc_lines) +
            "\n\nYou can search specific doctors or departments on our Doctors page, or ask me for any specialist!"
        ), False

    elif intent == "doctor_availability":
        if "doctor" in entities:
            doc_query = entities["doctor"].replace("Dr.", "").strip()
            doctor = Doctor.query.filter(Doctor.name.ilike(f"%{doc_query}%")).first()
            if doctor:
                return (
                    f"{doctor.name} ({doctor.specialization}) consults on:\n"
                    f"• Days: {doctor.available_days}\n"
                    f"• Timing: {doctor.start_time} to {doctor.end_time}\n"
                    f"• Location: {doctor.room_number}\n"
                    "Would you like to check available slots for tomorrow or another date?"
                ), False

        return (
            "To check doctor availability, please tell me the doctor's name or department, "
            "for example: 'When is Dr Sharma available?' or 'Check availability in Cardiology'."
        ), False

    elif intent == "appointment_booking":
        context = nlp_engine.get_context(session_id)
        context["step"] = "awaiting_booking_details"
        
        # Check what we already have
        doc_name = entities.get("doctor")
        dept_name = entities.get("department")
        date_str = entities.get("date")

        if doc_name and date_str:
            return (
                f"I can help you book with {doc_name} for {date_str}. "
                "Which preferred time would you like (e.g. 10:00 AM, 02:30 PM)? "
                "You can also use our online booking form on the Appointments page."
            ), False
        elif doc_name:
            return (
                f"Understood. Which date would you like to schedule your consultation with {doc_name}?"
            ), False
        elif dept_name:
            return (
                f"Great. We have top specialists in {dept_name}. "
                "Which doctor or date would you prefer?"
            ), False
        else:
            return (
                "I'd be glad to help you schedule a consultation. "
                "Which department or doctor would you like to visit?"
            ), False

    elif intent == "appointment_status":
        if user:
            apts = Appointment.query.filter_by(patient_id=user.id).order_by(Appointment.appointment_date.desc()).limit(3).all()
            if apts:
                lines = [f"• {a.id}: {a.doctor.name} on {a.appointment_date} at {a.appointment_time} [{a.status.upper()}]" for a in apts]
                return f"Here are your latest appointments:\n" + "\n".join(lines), False
            else:
                return "You currently have no scheduled appointments. Would you like to book one now?", False
        return (
            "To view your specific appointment status, please login to your patient account, "
            "or provide your Appointment ID (e.g. APT-202509-XXXX)."
        ), False

    elif intent == "appointment_cancel":
        return (
            "To cancel an appointment:\n"
            "1. Go to the 'Appointments' page in your patient account and click 'Cancel'.\n"
            "2. Or provide your Appointment ID here (e.g., 'Cancel appointment APT-202509-XXXX').\n"
            "Please note: Appointments can be cancelled up to 2 hours prior to the scheduled slot."
        ), False

    elif intent == "symptom_guidance":
        safety_flag = True
        return get_safe_symptom_guidance(raw_text), True

    elif intent == "department_recommendation":
        text_lower = raw_text.lower()
        matched_dept = None
        for symptom, dept in nlp_engine.symptom_department_map.items():
            if symptom in text_lower:
                matched_dept = dept
                break

        if matched_dept:
            return (
                f"Based on your query regarding symptoms, our {matched_dept} department is typically "
                f"best suited for evaluation.\n\n"
                f"Notice: This routing suggestion is general guidance and not a medical diagnosis. "
                f"Would you like me to show doctors available in {matched_dept}?"
                + GENERAL_MEDICAL_DISCLAIMER
            ), True
        else:
            return (
                "For general or unclassified symptoms, we recommend consulting our General Medicine department "
                "first. Our physicians can conduct an initial assessment and refer you to a specialist if needed."
                + GENERAL_MEDICAL_DISCLAIMER
            ), True

    elif intent == "faq":
        faqs = FAQ.query.limit(3).all()
        if faqs:
            faq_lines = [f"Q: {f.question}\nA: {f.answer}" for f in faqs]
            return "Here are some frequently asked questions:\n\n" + "\n\n".join(faq_lines), False
        return "You can explore our extensive categorized FAQ page for instant answers to visitor questions!", False

    # Default fallback
    return (
        "I'm here to assist you with hospital information, finding doctors, scheduling appointments, "
        "OPD timings, and hospital services. How can I help you today?"
    ), False

def _handle_booking_flow(message_text: str, entities: dict, context: dict, session_id: str):
    """Handles multi-turn appointment scheduling steps."""
    stored_entities = context.get("entities", {})
    stored_entities.update(entities)
    context["entities"] = stored_entities

    doc_name = stored_entities.get("doctor")
    dept_name = stored_entities.get("department")
    date_str = stored_entities.get("date")

    # If user provided a department in this turn
    if not dept_name and not doc_name:
        for dept in nlp_engine.departments:
            if dept in message_text.lower():
                dept_name = dept.title()
                stored_entities["department"] = dept_name
                break

    if not doc_name and not dept_name:
        return "Sure! Which department (like Cardiology, Dermatology, Orthopedics) or doctor would you like to consult?"

    if not date_str:
        return f"Got it. Which date would you prefer to visit (e.g. tomorrow, or YYYY-MM-DD)?"

    # If we have both doctor/dept and date:
    target_doctor = None
    if doc_name:
        doc_q = doc_name.replace("Dr.", "").strip()
        target_doctor = Doctor.query.filter(Doctor.name.ilike(f"%{doc_q}%")).first()
    elif dept_name:
        dept = Department.query.filter(Department.name.ilike(f"%{dept_name}%")).first()
        if dept and dept.doctors:
            target_doctor = dept.doctors[0]

    if target_doctor:
        context["step"] = "idle"  # reset flow
        return (
            f"Great! {target_doctor.name} ({target_doctor.department.name}) is scheduled on {target_doctor.available_days} "
            f"from {target_doctor.start_time} to {target_doctor.end_time}.\n"
            f"Target Date: {date_str}.\n\n"
            f"To complete your booking, please open the Appointments page or click 'Book Appointment' on {target_doctor.name}'s profile."
        )

    return f"We have noted your interest for {date_str}. Please visit our Doctors page to choose your doctor and pick your preferred time slot!"

def _save_chat_turn(session_id: str, user_msg: str, bot_resp: str, intent: str, confidence: float, safety_flag: bool):
    """Persist user message and bot response to database."""
    try:
        user_record = ChatMessage(
            session_id=session_id,
            sender="user",
            message=user_msg,
            created_at=datetime.now(timezone.utc)
        )
        bot_record = ChatMessage(
            session_id=session_id,
            sender="bot",
            message=bot_resp,
            intent=intent,
            confidence=confidence,
            safety_flag=safety_flag,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(user_record)
        db.session.add(bot_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[!] Error persisting chat message: {e}")
