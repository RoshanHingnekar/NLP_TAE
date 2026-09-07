"""
Hospital Assistant Chatbot - Main Flask Application
Serves REST APIs and frontend single-origin files.
"""
import os
import sys
import time
import logging

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

from backend.config import get_config
from backend.database import init_db, db
from backend.models import User, Department, Doctor, Appointment, FAQ, HospitalService, ChatSession, ChatMessage
from backend.nlp.chatbot import nlp_engine
from backend.services import (
    auth_service,
    doctor_service,
    appointment_service,
    hospital_service,
    chatbot_service
)

# Set up clean structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("HospitalAssistant")

def create_app(config_object=None):
    """Application factory pattern."""
    app = Flask(__name__, static_folder=None)
    
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(get_config())

    # Enable CORS
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Initialize Database
    init_db(app)

    # Initialize NLP model if not already loaded
    if nlp_engine.model is None:
        nlp_engine.load_model()

    # Request performance logging middleware
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request_info(response):
        if hasattr(request, "start_time"):
            duration = (time.time() - request.start_time) * 1000
            # Do not log sensitive credentials or health data in URL/body
            logger.info(f"{request.method} {request.path} {response.status_code} - {duration:.2f}ms")
        return response

    # -------------------------------------------------------------
    # JSON Error Handlers (Ensure APIs NEVER return HTML error pages)
    # -------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e.description if hasattr(e, "description") else e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden", "message": "Access restricted."}), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found", "message": f"Endpoint '{request.path}' not found."}), 404
        # If web request, serve index or redirect
        frontend_dir = app.config.get("FRONTEND_DIR")
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return send_file(index_file)
        return jsonify({"error": "Page Not Found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "A temporary server issue occurred."}), 500

    # -------------------------------------------------------------
    # Health Check Endpoint
    # -------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "ok",
            "environment": app.config.get("ENVIRONMENT", "development"),
            "database": "connected" if db.engine else "disconnected"
        }), 200

    # -------------------------------------------------------------
    # Authentication Endpoints
    # -------------------------------------------------------------
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        phone = data.get("phone", "").strip()
        role = data.get("role", "patient").strip()

        if not name or not email or not password:
            return jsonify({"error": "Validation failed", "message": "Name, email, and password are required."}), 400

        user, err = auth_service.register_user(name, email, password, phone, role)
        if err:
            return jsonify({"error": "Registration failed", "message": err}), 400

        token = auth_service.create_access_token(user)
        return jsonify({
            "message": "Registration successful.",
            "user": user.to_dict(),
            "token": token
        }), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"error": "Validation failed", "message": "Email and password are required."}), 400

        user, token, err = auth_service.authenticate_user(email, password)
        if err:
            return jsonify({"error": "Authentication failed", "message": err}), 401

        return jsonify({
            "message": "Login successful.",
            "user": user.to_dict(),
            "token": token
        }), 200

    @app.route("/api/auth/me", methods=["GET"])
    @auth_service.token_required
    def current_user(user):
        return jsonify({"user": user.to_dict()}), 200

    @app.route("/api/auth/profile", methods=["PUT"])
    @auth_service.token_required
    def update_profile(user):
        data = request.get_json() or {}
        if "name" in data and data["name"].strip():
            user.name = data["name"].strip()
        if "phone" in data:
            user.phone = data["phone"].strip()
        db.session.commit()
        return jsonify({"message": "Profile updated successfully.", "user": user.to_dict()}), 200

    # -------------------------------------------------------------
    # Hospital Public Information Endpoints
    # -------------------------------------------------------------
    @app.route("/api/hospital", methods=["GET"])
    def get_hospital():
        return jsonify(hospital_service.get_hospital_info()), 200

    @app.route("/api/departments", methods=["GET"])
    def get_departments():
        depts = hospital_service.get_all_departments()
        return jsonify([d.to_dict() for d in depts]), 200

    @app.route("/api/departments/<int:dept_id>", methods=["GET"])
    def get_department(dept_id):
        dept = hospital_service.get_department_by_id(dept_id)
        if not dept:
            return jsonify({"error": "Not Found", "message": "Department not found."}), 404
        return jsonify(dept.to_dict(include_doctors=True)), 200

    @app.route("/api/doctors", methods=["GET"])
    def get_doctors():
        dept_id = request.args.get("department_id", type=int)
        spec = request.args.get("specialization")
        search = request.args.get("search")
        docs = doctor_service.get_all_doctors(department_id=dept_id, specialization=spec, search=search)
        return jsonify([doc.to_dict() for doc in docs]), 200

    @app.route("/api/doctors/<int:doc_id>", methods=["GET"])
    def get_doctor(doc_id):
        doctor = doctor_service.get_doctor_by_id(doc_id)
        if not doctor:
            return jsonify({"error": "Not Found", "message": "Doctor not found."}), 404
        return jsonify(doctor.to_dict()), 200

    @app.route("/api/doctors/<int:doc_id>/availability", methods=["GET"])
    def doctor_availability(doc_id):
        date_param = request.args.get("date")
        if not date_param:
            return jsonify({"error": "Validation failed", "message": "Query param 'date' (YYYY-MM-DD) is required."}), 400

        data, err = doctor_service.get_doctor_availability(doc_id, date_param)
        if err:
            return jsonify({"error": "Doctor lookup failed", "message": err}), 404
        return jsonify(data), 200

    @app.route("/api/faqs", methods=["GET"])
    def get_faqs():
        category = request.args.get("category")
        search = request.args.get("search")
        faqs = hospital_service.get_all_faqs(category=category, search=search)
        return jsonify([f.to_dict() for f in faqs]), 200

    @app.route("/api/services", methods=["GET"])
    def get_services():
        srvs = hospital_service.get_all_services()
        return jsonify([s.to_dict() for s in srvs]), 200

    # -------------------------------------------------------------
    # Appointments Endpoints
    # -------------------------------------------------------------
    @app.route("/api/appointments", methods=["POST"])
    @auth_service.token_required
    def create_appointment(user):
        data = request.get_json() or {}
        doctor_id = data.get("doctor_id")
        appointment_date = data.get("appointment_date")
        appointment_time = data.get("appointment_time")
        reason = data.get("reason", "General Consultation")

        if not doctor_id or not appointment_date or not appointment_time:
            return jsonify({
                "error": "Validation failed",
                "message": "doctor_id, appointment_date, and appointment_time are required."
            }), 400

        apt, err = appointment_service.book_appointment(
            patient_id=user.id,
            doctor_id=int(doctor_id),
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason
        )
        if err:
            return jsonify({"error": "Booking failed", "message": err}), 400

        return jsonify({
            "message": "Appointment confirmed successfully!",
            "appointment": apt.to_dict()
        }), 201

    @app.route("/api/appointments", methods=["GET"])
    @auth_service.token_required
    def list_appointments(user):
        status = request.args.get("status")
        apts = appointment_service.get_user_appointments(user_id=user.id, role=user.role, status=status)
        return jsonify([a.to_dict() for a in apts]), 200

    @app.route("/api/appointments/<appointment_id>", methods=["GET"])
    @auth_service.token_required
    def get_appointment(user, appointment_id):
        apt = appointment_service.get_appointment_by_id(appointment_id)
        if not apt:
            return jsonify({"error": "Not Found", "message": "Appointment not found."}), 404
        if user.role == "patient" and apt.patient_id != user.id:
            return jsonify({"error": "Forbidden", "message": "Unauthorized access to appointment."}), 403
        return jsonify(apt.to_dict()), 200

    @app.route("/api/appointments/<appointment_id>", methods=["DELETE"])
    @auth_service.token_required
    def cancel_appointment(user, appointment_id):
        success, err = appointment_service.cancel_appointment(appointment_id, user.id, user.role)
        if not success:
            return jsonify({"error": "Cancellation failed", "message": err}), 400
        return jsonify({"message": f"Appointment {appointment_id} cancelled successfully."}), 200

    @app.route("/api/appointments/<appointment_id>/status", methods=["PUT"])
    @auth_service.roles_required("staff", "admin")
    def update_appointment_status(user, appointment_id):
        data = request.get_json() or {}
        new_status = data.get("status")
        if not new_status:
            return jsonify({"error": "Validation failed", "message": "Field 'status' is required."}), 400

        apt, err = appointment_service.update_appointment_status(appointment_id, new_status)
        if err:
            return jsonify({"error": "Update failed", "message": err}), 400

        return jsonify({"message": "Appointment status updated.", "appointment": apt.to_dict()}), 200

    # -------------------------------------------------------------
    # Chat Endpoints
    # -------------------------------------------------------------
    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        session_id = data.get("session_id")

        if not message:
            return jsonify({"error": "Validation failed", "message": "Message text is required."}), 400

        user = auth_service.get_current_user_from_token()
        result = chatbot_service.process_chat_message(message, session_id, user)
        return jsonify(result), 200

    @app.route("/api/chat/history", methods=["GET"])
    def chat_history():
        session_id = request.args.get("session_id")
        user = auth_service.get_current_user_from_token()

        if session_id:
            session = ChatSession.query.get(session_id)
            if not session:
                return jsonify({"messages": [], "session_id": session_id}), 200
            return jsonify(session.to_dict(include_messages=True)), 200

        # If user authenticated, return their recent sessions
        if user:
            sessions = ChatSession.query.filter_by(user_id=user.id).order_by(ChatSession.updated_at.desc()).limit(10).all()
            return jsonify([s.to_dict(include_messages=True) for s in sessions]), 200

        return jsonify({"messages": []}), 200

    # -------------------------------------------------------------
    # Admin Endpoints
    # -------------------------------------------------------------
    @app.route("/api/admin/doctors", methods=["POST"])
    @auth_service.roles_required("admin")
    def admin_create_doctor(user):
        data = request.get_json() or {}
        doctor, err = doctor_service.create_doctor(data)
        if err:
            return jsonify({"error": "Creation failed", "message": err}), 400
        return jsonify({"message": "Doctor created successfully.", "doctor": doctor.to_dict()}), 201

    @app.route("/api/admin/doctors/<int:doc_id>", methods=["PUT"])
    @auth_service.roles_required("admin")
    def admin_update_doctor(user, doc_id):
        data = request.get_json() or {}
        doctor, err = doctor_service.update_doctor(doc_id, data)
        if err:
            return jsonify({"error": "Update failed", "message": err}), 400
        return jsonify({"message": "Doctor updated successfully.", "doctor": doctor.to_dict()}), 200

    @app.route("/api/admin/doctors/<int:doc_id>", methods=["DELETE"])
    @auth_service.roles_required("admin")
    def admin_delete_doctor(user, doc_id):
        success, err = doctor_service.delete_doctor(doc_id)
        if not success:
            return jsonify({"error": "Delete failed", "message": err}), 400
        return jsonify({"message": "Doctor deleted successfully."}), 200

    @app.route("/api/admin/departments", methods=["POST"])
    @auth_service.roles_required("admin")
    def admin_create_dept(user):
        data = request.get_json() or {}
        dept, err = hospital_service.create_department(data)
        if err:
            return jsonify({"error": "Creation failed", "message": err}), 400
        return jsonify({"message": "Department created successfully.", "department": dept.to_dict()}), 201

    @app.route("/api/admin/departments/<int:dept_id>", methods=["PUT"])
    @auth_service.roles_required("admin")
    def admin_update_dept(user, dept_id):
        data = request.get_json() or {}
        dept, err = hospital_service.update_department(dept_id, data)
        if err:
            return jsonify({"error": "Update failed", "message": err}), 400
        return jsonify({"message": "Department updated successfully.", "department": dept.to_dict()}), 200

    @app.route("/api/admin/departments/<int:dept_id>", methods=["DELETE"])
    @auth_service.roles_required("admin")
    def admin_delete_dept(user, dept_id):
        success, err = hospital_service.delete_department(dept_id)
        if not success:
            return jsonify({"error": "Delete failed", "message": err}), 400
        return jsonify({"message": "Department deleted successfully."}), 200

    @app.route("/api/admin/faqs", methods=["POST"])
    @auth_service.roles_required("admin")
    def admin_create_faq(user):
        data = request.get_json() or {}
        faq, err = hospital_service.create_faq(data)
        if err:
            return jsonify({"error": "Creation failed", "message": err}), 400
        return jsonify({"message": "FAQ created successfully.", "faq": faq.to_dict()}), 201

    @app.route("/api/admin/faqs/<int:faq_id>", methods=["PUT"])
    @auth_service.roles_required("admin")
    def admin_update_faq(user, faq_id):
        data = request.get_json() or {}
        faq, err = hospital_service.update_faq(faq_id, data)
        if err:
            return jsonify({"error": "Update failed", "message": err}), 400
        return jsonify({"message": "FAQ updated successfully.", "faq": faq.to_dict()}), 200

    @app.route("/api/admin/faqs/<int:faq_id>", methods=["DELETE"])
    @auth_service.roles_required("admin")
    def admin_delete_faq(user, faq_id):
        success, err = hospital_service.delete_faq(faq_id)
        if not success:
            return jsonify({"error": "Delete failed", "message": err}), 400
        return jsonify({"message": "FAQ deleted successfully."}), 200

    @app.route("/api/admin/services", methods=["POST"])
    @auth_service.roles_required("admin")
    def admin_create_service(user):
        data = request.get_json() or {}
        srv, err = hospital_service.create_service(data)
        if err:
            return jsonify({"error": "Creation failed", "message": err}), 400
        return jsonify({"message": "Service created successfully.", "service": srv.to_dict()}), 201

    @app.route("/api/admin/services/<int:srv_id>", methods=["PUT"])
    @auth_service.roles_required("admin")
    def admin_update_service(user, srv_id):
        data = request.get_json() or {}
        srv, err = hospital_service.update_service(srv_id, data)
        if err:
            return jsonify({"error": "Update failed", "message": err}), 400
        return jsonify({"message": "Service updated successfully.", "service": srv.to_dict()}), 200

    @app.route("/api/admin/services/<int:srv_id>", methods=["DELETE"])
    @auth_service.roles_required("admin")
    def admin_delete_service(user, srv_id):
        success, err = hospital_service.delete_service(srv_id)
        if not success:
            return jsonify({"error": "Delete failed", "message": err}), 400
        return jsonify({"message": "Service deleted successfully."}), 200

    @app.route("/api/admin/analytics", methods=["GET"])
    @auth_service.roles_required("admin")
    def admin_analytics(user):
        data = hospital_service.get_admin_analytics()
        return jsonify(data), 200

    # -------------------------------------------------------------
    # Frontend Single-Origin Serving (Crucial for Render Deployment)
    # -------------------------------------------------------------
    frontend_dir = app.config.get("FRONTEND_DIR")

    @app.route("/", methods=["GET"])
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>", methods=["GET"])
    def serve_static_or_page(path):
        # Prevent accessing files outside frontend_dir
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(frontend_dir, path)

        # Allow omitting .html in URLs (e.g. /chatbot, /doctors, /admin)
        html_file = os.path.join(frontend_dir, f"{path}.html")
        if os.path.isfile(html_file):
            return send_from_directory(frontend_dir, f"{path}.html")

        # Fallback to index.html
        return send_from_directory(frontend_dir, "index.html")

    return app

# WSGI entry point for Gunicorn on Render
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("ENVIRONMENT", "development").lower() == "development"
    print(f"[OK] Hospital Assistant Chatbot server starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
