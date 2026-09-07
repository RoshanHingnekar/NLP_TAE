"""
Database Seeding Script for Hospital Assistant Chatbot
Creates tables and populates comprehensive DEMO hospital data:
- 13 Clinical Departments
- 16 Experienced Specialist Doctors
- 32 Categorized FAQs
- 10 Hospital Services
- Pre-configured Admin, Staff, and Patient demo accounts
- Sample Appointments and Chat History for analytics
"""
import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app
from backend.database import db
from backend.models import User, Department, Doctor, Appointment, FAQ, HospitalService, ChatSession, ChatMessage
from backend.services.auth_service import hash_password
from backend.calculator import generate_slots

def seed_database():
    app = create_app()
    with app.app_context():
        print("[*] Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(email="admin@carebridge.demo").first():
            print("[!] Database appears to be already seeded. Re-verifying...")
            # We will ensure all essential tables have records

        # 1. Seed Users
        print("[*] Seeding default accounts (Admin, Staff, Patient)...")
        users_data = [
            {
                "name": "Dr. Arthur Vance (Chief Admin)",
                "email": "admin@carebridge.demo",
                "password": "Admin@123",
                "phone": "+1 (555) 019-1001",
                "role": "admin"
            },
            {
                "name": "Nurse Evelyn Reed (Desk Staff)",
                "email": "staff@carebridge.demo",
                "password": "Staff@123",
                "phone": "+1 (555) 019-1002",
                "role": "staff"
            },
            {
                "name": "Alex Mercer (Demo Patient)",
                "email": "patient@carebridge.demo",
                "password": "Patient@123",
                "phone": "+1 (555) 019-2001",
                "role": "patient"
            },
            {
                "name": "Sarah Jenkins (Demo Patient)",
                "email": "sarah@carebridge.demo",
                "password": "Patient@123",
                "phone": "+1 (555) 019-2002",
                "role": "patient"
            }
        ]

        created_users = {}
        for u in users_data:
            existing = User.query.filter_by(email=u["email"]).first()
            if not existing:
                new_u = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    phone=u["phone"],
                    role=u["role"]
                )
                db.session.add(new_u)
                db.session.flush()
                created_users[u["email"]] = new_u
            else:
                created_users[u["email"]] = existing

        # 2. Seed Departments (13 Required)
        print("[*] Seeding 13 Clinical Departments...")
        departments_data = [
            {
                "name": "Cardiology",
                "description": "Comprehensive cardiac evaluations, interventional cardiology, ECG, echocardiography, and preventive heart care.",
                "location": "Wing A, 2nd Floor",
                "opd_timing": "08:00 AM - 05:00 PM (Mon-Sat)"
            },
            {
                "name": "Neurology",
                "description": "Specialized diagnosis and treatment of brain, spinal cord, headache disorders, stroke rehabilitation, and neuropathy.",
                "location": "Wing B, 3rd Floor",
                "opd_timing": "09:00 AM - 04:30 PM (Mon-Fri)"
            },
            {
                "name": "Orthopedics",
                "description": "Joint replacement, fracture trauma care, spine surgery, sports medicine, and arthroscopy.",
                "location": "Wing A, 1st Floor",
                "opd_timing": "08:30 AM - 05:00 PM (Mon-Sat)"
            },
            {
                "name": "Dermatology",
                "description": "Clinical skincare, allergy patch testing, eczema, psoriasis therapies, laser skin treatment, and cosmetology.",
                "location": "Wing C, 2nd Floor",
                "opd_timing": "09:00 AM - 05:00 PM (Mon-Sat)"
            },
            {
                "name": "Pediatrics",
                "description": "Child healthcare, newborn intensive care, routine pediatric vaccinations, growth monitoring, and pediatric surgery.",
                "location": "Wing D, Ground Floor",
                "opd_timing": "08:00 AM - 06:00 PM (Daily)"
            },
            {
                "name": "Gynecology & Obstetrics",
                "description": "Maternal care, high-risk pregnancy management, fetal monitoring, fertility guidance, and gynecological surgeries.",
                "location": "Wing D, 2nd Floor",
                "opd_timing": "08:30 AM - 05:00 PM (Mon-Sat)"
            },
            {
                "name": "ENT (Otolaryngology)",
                "description": "Ear, nose, throat, head and neck surgery, audiology testing, sinus endoscopy, and voice therapies.",
                "location": "Wing B, 1st Floor",
                "opd_timing": "09:00 AM - 04:00 PM (Mon-Fri)"
            },
            {
                "name": "Ophthalmology",
                "description": "Vision assessment, micro-incision cataract surgery, glaucoma screening, retina care, and corneal clinics.",
                "location": "Wing C, 1st Floor",
                "opd_timing": "08:30 AM - 04:30 PM (Mon-Sat)"
            },
            {
                "name": "General Medicine",
                "description": "Primary healthcare, management of hypertension, diabetes, seasonal fevers, infectious diseases, and executive checkups.",
                "location": "Main Atrium, Ground Floor",
                "opd_timing": "08:00 AM - 08:00 PM (Daily)"
            },
            {
                "name": "General Surgery",
                "description": "Minimally invasive laparoscopic procedures, hernia repair, gallbladder surgery, and emergency abdominal trauma.",
                "location": "Wing A, 3rd Floor",
                "opd_timing": "09:00 AM - 05:00 PM (Mon-Sat)"
            },
            {
                "name": "Dentistry",
                "description": "Dental restorations, endodontics (root canal), orthodontics, periodontics, and maxillofacial surgery.",
                "location": "Wing C, Ground Floor",
                "opd_timing": "09:00 AM - 06:00 PM (Mon-Sat)"
            },
            {
                "name": "Radiology & Imaging",
                "description": "Digital X-Rays, 3.0T MRI, 128-Slice High Speed CT, ultrasound sonography, and image-guided biopsies.",
                "location": "Basement 1, Diagnostic Center",
                "opd_timing": "24/7 Round the Clock (OPD: 08:00 AM - 08:00 PM)"
            },
            {
                "name": "Emergency Medicine",
                "description": "Level-1 emergency trauma care, acute cardiac resuscitation, stroke management, and rapid triage.",
                "location": "Ground Floor, Emergency Ambulance Bay",
                "opd_timing": "24 Hours / 7 Days a Week"
            }
        ]

        dept_map = {}
        for d in departments_data:
            existing_d = Department.query.filter_by(name=d["name"]).first()
            if not existing_d:
                new_d = Department(
                    name=d["name"],
                    description=d["description"],
                    location=d["location"],
                    opd_timing=d["opd_timing"]
                )
                db.session.add(new_d)
                db.session.flush()
                dept_map[d["name"]] = new_d
            else:
                dept_map[d["name"]] = existing_d

        # 3. Seed Doctors (16 DEMO Doctors across Departments)
        print("[*] Seeding 16 Specialist Doctors (DEMO DATA)...")
        doctors_data = [
            {
                "name": "Dr. Rajesh Sharma",
                "dept": "Cardiology",
                "specialization": "Senior Interventional Cardiologist",
                "qualification": "MD, DM (Cardiology), FACC",
                "experience": "16 Years",
                "available_days": "Monday, Tuesday, Wednesday, Friday",
                "start_time": "09:00",
                "end_time": "14:00",
                "consultation_fee": 65.0,
                "room_number": "Room 201, Wing A",
                "status": "active"
            },
            {
                "name": "Dr. Ananya Verma",
                "dept": "Cardiology",
                "specialization": "Non-Invasive Cardiologist & Echocardiography",
                "qualification": "MD, DNB (Cardiology)",
                "experience": "11 Years",
                "available_days": "Tuesday, Thursday, Saturday",
                "start_time": "13:00",
                "end_time": "18:00",
                "consultation_fee": 55.0,
                "room_number": "Room 203, Wing A",
                "status": "active"
            },
            {
                "name": "Dr. Vikram Singh",
                "dept": "Neurology",
                "specialization": "Consultant Neurologist & Stroke Specialist",
                "qualification": "MBBS, MD (Medicine), DM (Neurology)",
                "experience": "14 Years",
                "available_days": "Monday, Wednesday, Friday",
                "start_time": "10:00",
                "end_time": "16:00",
                "consultation_fee": 70.0,
                "room_number": "Room 304, Wing B",
                "status": "active"
            },
            {
                "name": "Dr. Priya Patel",
                "dept": "Dermatology",
                "specialization": "Clinical Dermatologist & Aesthetician",
                "qualification": "MBBS, MD (Dermatology)",
                "experience": "9 Years",
                "available_days": "Monday, Tuesday, Thursday, Saturday",
                "start_time": "09:30",
                "end_time": "15:30",
                "consultation_fee": 50.0,
                "room_number": "Room 210, Wing C",
                "status": "active"
            },
            {
                "name": "Dr. Rohan Mehta",
                "dept": "Orthopedics",
                "specialization": "Joint Replacement & Arthroscopy Surgeon",
                "qualification": "MS (Orthopedics), MCh (Ortho, UK)",
                "experience": "18 Years",
                "available_days": "Monday, Tuesday, Thursday, Friday",
                "start_time": "09:00",
                "end_time": "15:00",
                "consultation_fee": 60.0,
                "room_number": "Room 105, Wing A",
                "status": "active"
            },
            {
                "name": "Dr. Meera Nambiar",
                "dept": "Pediatrics",
                "specialization": "Senior Consultant Pediatrician & Neonatologist",
                "qualification": "MBBS, MD (Pediatrics), Fellowship Neonatology",
                "experience": "13 Years",
                "available_days": "Monday, Wednesday, Thursday, Saturday",
                "start_time": "08:30",
                "end_time": "14:30",
                "consultation_fee": 45.0,
                "room_number": "Room 012, Wing D",
                "status": "active"
            },
            {
                "name": "Dr. Sunita Deshmukh",
                "dept": "Gynecology & Obstetrics",
                "specialization": "Obstetrician & High-Risk Pregnancy Specialist",
                "qualification": "MBBS, MS (OBG), FICOG",
                "experience": "15 Years",
                "available_days": "Monday, Tuesday, Wednesday, Friday",
                "start_time": "09:00",
                "end_time": "15:00",
                "consultation_fee": 55.0,
                "room_number": "Room 215, Wing D",
                "status": "active"
            },
            {
                "name": "Dr. Alok Banerjee",
                "dept": "ENT (Otolaryngology)",
                "specialization": "ENT & Head-Neck Endoscopic Surgeon",
                "qualification": "MBBS, MS (ENT), DLO",
                "experience": "12 Years",
                "available_days": "Tuesday, Wednesday, Thursday, Saturday",
                "start_time": "10:00",
                "end_time": "16:00",
                "consultation_fee": 45.0,
                "room_number": "Room 108, Wing B",
                "status": "active"
            },
            {
                "name": "Dr. Kavita Joshi",
                "dept": "Ophthalmology",
                "specialization": "Cataract, Cornea & Refractive Surgeon",
                "qualification": "MBBS, MS (Ophthalmology), FICO",
                "experience": "10 Years",
                "available_days": "Monday, Wednesday, Friday, Saturday",
                "start_time": "09:00",
                "end_time": "14:00",
                "consultation_fee": 45.0,
                "room_number": "Room 112, Wing C",
                "status": "active"
            },
            {
                "name": "Dr. Harshavardhan Rao",
                "dept": "General Medicine",
                "specialization": "Consultant Physician & Diabetologist",
                "qualification": "MBBS, MD (General Medicine)",
                "experience": "20 Years",
                "available_days": "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday",
                "start_time": "08:00",
                "end_time": "16:00",
                "consultation_fee": 40.0,
                "room_number": "Room 004, Main Atrium",
                "status": "active"
            },
            {
                "name": "Dr. Siddharth Kapoor",
                "dept": "General Surgery",
                "specialization": "Advanced Laparoscopic & GI Surgeon",
                "qualification": "MS (General Surgery), FMAS, FIAGES",
                "experience": "14 Years",
                "available_days": "Monday, Tuesday, Thursday, Friday",
                "start_time": "11:00",
                "end_time": "17:00",
                "consultation_fee": 60.0,
                "room_number": "Room 302, Wing A",
                "status": "active"
            },
            {
                "name": "Dr. Tanya Sen",
                "dept": "Dentistry",
                "specialization": "Cosmetic Dentist & Root Canal Specialist",
                "qualification": "BDS, MDS (Conservative Dentistry)",
                "experience": "8 Years",
                "available_days": "Monday, Wednesday, Thursday, Saturday",
                "start_time": "10:00",
                "end_time": "17:00",
                "consultation_fee": 35.0,
                "room_number": "Room 018, Wing C",
                "status": "active"
            },
            {
                "name": "Dr. Manish Kulkarni",
                "dept": "Radiology & Imaging",
                "specialization": "Chief Diagnostic & Interventional Radiologist",
                "qualification": "MD (Radiodiagnosis), FRCR (UK)",
                "experience": "17 Years",
                "available_days": "Monday, Tuesday, Wednesday, Thursday, Friday",
                "start_time": "08:00",
                "end_time": "16:00",
                "consultation_fee": 50.0,
                "room_number": "Basement Diagnostic Wing",
                "status": "active"
            },
            {
                "name": "Dr. Neha Malhotra",
                "dept": "Emergency Medicine",
                "specialization": "Emergency Medicine & Critical Care Physician",
                "qualification": "MBBS, MEM (Emergency Medicine)",
                "experience": "9 Years",
                "available_days": "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday",
                "start_time": "00:00",
                "end_time": "23:59",
                "consultation_fee": 45.0,
                "room_number": "Casualty Trauma Bay",
                "status": "active"
            },
            {
                "name": "Dr. Vivek Choudhury",
                "dept": "General Medicine",
                "specialization": "Internal Medicine & Infectious Disease Consultant",
                "qualification": "MD (Medicine), Postgrad ID",
                "experience": "11 Years",
                "available_days": "Tuesday, Thursday, Friday, Saturday",
                "start_time": "12:00",
                "end_time": "20:00",
                "consultation_fee": 40.0,
                "room_number": "Room 006, Main Atrium",
                "status": "active"
            },
            {
                "name": "Dr. Deepa Nair",
                "dept": "Pediatrics",
                "specialization": "Pediatric Pulmonology & Allergy",
                "qualification": "MBBS, DCH, DNB (Pediatrics)",
                "experience": "10 Years",
                "available_days": "Monday, Tuesday, Friday, Saturday",
                "start_time": "14:00",
                "end_time": "19:00",
                "consultation_fee": 45.0,
                "room_number": "Room 014, Wing D",
                "status": "active"
            }
        ]

        created_doctors = []
        for doc in doctors_data:
            dept_obj = dept_map.get(doc["dept"])
            if dept_obj:
                existing_doc = Doctor.query.filter_by(name=doc["name"]).first()
                if not existing_doc:
                    new_doc = Doctor(
                        name=doc["name"],
                        department_id=dept_obj.id,
                        specialization=doc["specialization"],
                        qualification=doc["qualification"],
                        experience=doc["experience"],
                        available_days=doc["available_days"],
                        start_time=doc["start_time"],
                        end_time=doc["end_time"],
                        consultation_fee=doc["consultation_fee"],
                        room_number=doc["room_number"],
                        status=doc["status"]
                    )
                    db.session.add(new_doc)
                    db.session.flush()
                    created_doctors.append(new_doc)
                else:
                    created_doctors.append(existing_doc)

        # 4. Seed FAQs (32 Comprehensive FAQs across 7 Categories)
        print("[*] Seeding 32 FAQs across 7 clinical and administrative categories...")
        faqs_data = [
            # General
            ("What are the general hospital visiting hours?", "General inpatient wards allow visitors between 04:00 PM and 07:00 PM daily. ICU/CCU visiting is restricted to 11:00 AM - 12:00 PM and 05:00 PM - 06:00 PM with one visitor pass.", "General"),
            ("Is CareBridge hospital accredited and licensed?", "Yes, CareBridge Demo Hospital is fully accredited for NABH, JCI quality standards, and follows ISO healthcare hygiene protocols.", "General"),
            ("Where is the hospital admission desk located?", "The Central Admissions and Discharge Desk is located in the Main Atrium on the Ground Floor, open 24/7.", "General"),
            ("Is wheelchair assistance available upon arrival?", "Yes, complimentary wheelchair assistance and patient porters are stationed at the main entrance porch 24 hours a day.", "General"),
            ("Does the hospital provide Wi-Fi for patients?", "Complimentary high-speed Wi-Fi ('CareBridge-Guest') is available throughout outpatient lounges, patient rooms, and cafeteria.", "General"),

            # Appointments
            ("How do I book an appointment with a doctor?", "You can book directly through our online Appointments page, use our AI Hospital Assistant Chatbot, or call our appointments helpline at +1 (555) 019-2834.", "Appointments"),
            ("Can I cancel or reschedule my appointment?", "Yes, appointments can be cancelled or rescheduled up to 2 hours prior to the slot from your patient dashboard with zero cancellation fees.", "Appointments"),
            ("What documents should I bring for my doctor visit?", "Please carry a valid photo ID, your insurance card, appointment confirmation message/ID, and any previous medical or lab records.", "Appointments"),
            ("Can I book same-day appointments?", "Yes, same-day appointment slots are available based on doctor availability. In urgent cases, the 24/7 Emergency Casualty is always open.", "Appointments"),
            ("What is the consultation fee structure?", "Consultation fees range from $35 to $70 depending on the specialist's qualification. An itemized invoice is provided upon booking.", "Appointments"),

            # Doctors
            ("How qualified are the doctors at CareBridge?", "All our consultants hold board-certified postgraduate degrees (MD, MS, DM, MCh, or equivalent international fellowships) with extensive clinical experience.", "Doctors"),
            ("Can I consult a doctor online via teleconsultation?", "Yes, our telemedicine portal supports secure video consultations. You can select 'Teleconsultation' during appointment booking.", "Doctors"),
            ("How can I check when a doctor is available?", "Visit our Doctors page to search by doctor name or specialty, or ask the Hospital Assistant chatbot (e.g. 'When is Dr Sharma available?').", "Doctors"),
            ("Can I request a second medical opinion?", "Absolutely. You can request a multidisciplinary tumor board or specialist second opinion through our Medical Records desk.", "Doctors"),

            # Departments
            ("What clinical departments are available?", "We feature 13 major specialties: Cardiology, Neurology, Orthopedics, Dermatology, Pediatrics, Gynecology, ENT, Ophthalmology, General Medicine, General Surgery, Dentistry, Radiology, and Emergency.", "Departments"),
            ("Which department should I visit for unexplained fever?", "Our General Medicine department is best suited for fevers, viral infections, and diagnostic workups.", "Departments"),
            ("Do you have a dedicated pediatric emergency department?", "Yes, our Level-1 Emergency has a specialized pediatric resuscitation bay staffed with trained pediatric intensivists.", "Departments"),
            ("Where is the Orthopedics department located?", "Orthopedics and Fracture Clinic is located on the 1st Floor of Wing A, with direct elevator access from Radiology.", "Departments"),

            # Billing
            ("What payment modes are accepted at billing counters?", "We accept all major credit/debit cards (Visa, MasterCard, Amex), UPI QR codes, Net Banking, and Cash.", "Billing"),
            ("How do I obtain an itemized discharge bill?", "The Billing Department provides a detailed itemized bill during discharge. You can also download PDF summaries from your patient portal.", "Billing"),
            ("Is estimated cost of surgery provided beforehand?", "Yes, our Financial Counseling desk provides a formal written estimate of treatment, surgery, and bed charges prior to planned admissions.", "Billing"),
            ("Are payment installments or EMI options available?", "Yes, 0% interest EMI options are available for major surgeries through partner healthcare financing providers.", "Billing"),

            # Insurance
            ("Which insurance providers and TPAs are empanelled?", "We support 30+ insurance companies including Star Health, HDFC ERGO, Max Bupa, ICICI Lombard, Medi Assist, Paramount TPA, and corporate insurances.", "Insurance"),
            ("How does cashless hospitalization work?", "Submit your health card and doctor's admission advice at our 24/7 TPA Desk. We initiate electronic pre-authorization within 60 minutes.", "Insurance"),
            ("What happens if cashless pre-authorization is denied?", "You may settle the bill directly upon discharge and claim complete reimbursement from your insurer using the claim docket we provide.", "Insurance"),
            ("Does government health insurance cover treatment?", "Yes, CareBridge is empanelled under recognized state and central government healthcare security schemes.", "Insurance"),

            # Facilities
            ("Is the emergency room open on weekends and holidays?", "Yes, our Emergency Medicine and Trauma department is fully operational 24 hours a day, 365 days a year.", "Facilities"),
            ("Where is the 24/7 pharmacy situated?", "The main outpatient and emergency pharmacy is on the Ground Floor next to the main entrance lobby.", "Facilities"),
            ("Do you offer blood bank and transfusion services?", "Yes, our licensed 24/7 Blood Bank provides packed red cells, fresh frozen plasma, platelets, and component apheresis.", "Facilities"),
            ("Are cafeteria and food services available for attendants?", "A multi-cuisine cafeteria is situated on the 4th Floor serving healthy meals from 07:00 AM to 10:30 PM. 24/7 coffee kiosks are in the lobby.", "Facilities"),
            ("What diagnostic imaging scans are available in-house?", "We house a 3.0 Tesla MRI, 128-Slice Low Dose CT Scanner, Digital 3D Mammography, Color Doppler Ultrasonography, and DEXA scans.", "Facilities"),
            ("How can I book an ambulance for an emergency?", "Call our dedicated 24/7 Trauma Ambulance dispatch directly at +1 (555) 019-0108. GPS tracking is provided via SMS.", "Facilities")
        ]

        for q, a, cat in faqs_data:
            if not FAQ.query.filter_by(question=q).first():
                db.session.add(FAQ(question=q, answer=a, category=cat))

        # 5. Seed Hospital Services (10 Essential Services)
        print("[*] Seeding 10 Hospital Services...")
        services_data = [
            ("24/7 Emergency & Level-1 Trauma Care", "Comprehensive acute trauma resuscitation, triage, cardiac arrest response, and emergency surgical theatres.", "Ground Floor, Wing A", "24/7 Round the Clock", "+1 (555) 019-9911"),
            ("Intensive Care Units (ICU, CCU, PICU)", "State-of-the-art multi-bed critical care units with advanced ventilators, continuous hemodynamic monitoring, and 1:1 nurse-to-patient ratio.", "Wing B, 4th Floor", "24/7 Round the Clock", "+1 (555) 019-1040"),
            ("24/7 In-House Outpatient Pharmacy", "Fully licensed pharmacy offering authentic medicines, surgical consumables, cold-chain vaccines, and bedside medication distribution.", "Ground Floor Lobby", "24/7 Round the Clock", "+1 (555) 019-1050"),
            ("Automated Pathology & Diagnostic Lab", "Advanced automated clinical biochemistry, hematology, microbiology, histopathology, and genomic molecular testing.", "1st Floor, Diagnostic Wing", "24/7 (Reports in 4h)", "+1 (555) 019-1060"),
            ("Radiology & High-Speed Imaging Center", "Digital 3.0 Tesla MRI, 128-Slice CT scans, 4D Ultrasonography, and emergency interventional radiology.", "Basement 1", "24/7 Round the Clock", "+1 (555) 019-1070"),
            ("Licensed Blood Bank & Component Separation", "Voluntary blood donor drives, nucleic acid testing (NAT), cryoprecipitate, platelets, and emergency uncrossmatched blood.", "Basement 1, Wing B", "24/7 Round the Clock", "+1 (555) 019-1080"),
            ("Dialysis and Renal Care Center", "High-flux hemodialysis machines with automated disinfection, peritoneal dialysis guidance, and nephrology monitoring.", "Wing C, 3rd Floor", "06:00 AM - 10:00 PM", "+1 (555) 019-1090"),
            ("Physiotherapy & Physical Rehabilitation", "Post-operative orthopedic rehabilitation, stroke neuro-rehab, sports injury therapies, and electrotherapy suites.", "Wing A, Ground Floor", "08:00 AM - 07:00 PM", "+1 (555) 019-1095"),
            ("Trauma Ambulance 24/7 Service", "Fleet of advanced life support (ALS) and basic life support (BLS) ambulances equipped with mobile defibrillators and oxygen.", "Emergency Bay", "24/7 Round the Clock", "+1 (555) 019-0108"),
            ("Executive Preventive Health Checkup Center", "Customized wellness packages, executive screening, cardiac risk profiling, and personalized dietary consultations.", "Main Atrium, 2nd Floor", "07:30 AM - 04:00 PM", "+1 (555) 019-1030")
        ]

        for name, desc, loc, timing, contact in services_data:
            if not HospitalService.query.filter_by(name=name).first():
                db.session.add(HospitalService(
                    name=name,
                    description=desc,
                    location=loc,
                    timing=timing,
                    contact=contact
                ))

        db.session.commit()

        # 6. Seed Sample Appointments and Chat History for Rich Analytics
        print("[*] Seeding sample appointments and chat sessions for analytics...")
        patient_user = created_users.get("patient@carebridge.demo")
        sarah_user = created_users.get("sarah@carebridge.demo")

        if patient_user and created_doctors:
            today_str = datetime.now().strftime("%Y-%m-%d")
            tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            sample_apts = [
                ("APT-202509-1001", patient_user.id, created_doctors[0].id, today_str, "10:00", "Annual cardiac checkup & ECG review", "confirmed"),
                ("APT-202509-1002", patient_user.id, created_doctors[3].id, tomorrow_str, "11:30", "Skin allergy rash evaluation", "confirmed"),
                ("APT-202509-1003", sarah_user.id, created_doctors[4].id, yesterday_str, "09:30", "Knee joint stiffness and physiotherapy follow-up", "completed"),
                ("APT-202509-1004", sarah_user.id, created_doctors[5].id, today_str, "14:00", "Child vaccination and growth check", "confirmed"),
                ("APT-202509-1005", patient_user.id, created_doctors[2].id, yesterday_str, "15:00", "Migraine consultation", "cancelled")
            ]

            for aid, pid, did, adate, atime, r, st in sample_apts:
                if not Appointment.query.get(aid):
                    db.session.add(Appointment(
                        id=aid,
                        patient_id=pid,
                        doctor_id=did,
                        appointment_date=adate,
                        appointment_time=atime,
                        reason=r,
                        status=st
                    ))

        # Sample Chat Session & Messages
        demo_session_id = "demo-session-analytics-01"
        if not ChatSession.query.get(demo_session_id):
            session = ChatSession(id=demo_session_id, user_id=patient_user.id if patient_user else None)
            db.session.add(session)
            db.session.flush()

            demo_messages = [
                ("user", "Hello assistant", "greeting", 0.99, False),
                ("bot", "Hello! I'm your CareBridge Hospital Assistant. How can I help you today?", "greeting", 0.99, False),
                ("user", "What are the OPD timings?", "opd_timings", 0.96, False),
                ("bot", "Our Outpatient Department (OPD) operates Monday to Saturday 08:00 AM - 08:00 PM.", "opd_timings", 0.96, False),
                ("user", "Find a doctor in cardiology", "doctor_information", 0.91, False),
                ("bot", "Doctors in Cardiology: Dr. Rajesh Sharma and Dr. Ananya Verma.", "doctor_information", 0.91, False),
                ("user", "I have severe chest pain and cannot breathe", "emergency", 1.00, True),
                ("bot", "⚠ EMERGENCY NOTICE\nThis situation may require urgent medical attention. Please contact your local emergency services immediately.", "emergency", 1.00, True)
            ]

            for sender, msg, intent, conf, safety in demo_messages:
                db.session.add(ChatMessage(
                    session_id=demo_session_id,
                    sender=sender,
                    message=msg,
                    intent=intent,
                    confidence=conf,
                    safety_flag=safety,
                    created_at=datetime.now(timezone.utc)
                ))

        db.session.commit()
        print("[OK] Database seeded successfully!")
        print("  - Admin:   admin@carebridge.demo   / Admin@123")
        print("  - Staff:   staff@carebridge.demo   / Staff@123")
        print("  - Patient: patient@carebridge.demo / Patient@123")

if __name__ == "__main__":
    seed_database()
