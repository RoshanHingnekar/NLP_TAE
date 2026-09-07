"""
NLP Chatbot Inference Engine
Handles text normalization, intent classification with confidence scoring,
entity extraction, multi-turn dialogue context, and response generation.
"""
import os
import re
from datetime import datetime, timedelta
import joblib

from backend.nlp.safety import detect_emergency, get_emergency_response, get_safe_symptom_guidance, GENERAL_MEDICAL_DISCLAIMER

# In-memory session context storage for multi-turn conversations
# Maps session_id -> { "step": str, "entities": dict, "last_intent": str, "updated_at": float }
SESSION_CONTEXTS = {}

class HospitalNLP:
    def __init__(self, model_dir=None):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        self.model_dir = model_dir or os.path.join(base_dir, "model")
        self.model = None
        self.vectorizer = None
        self.load_model()

        # Known clinical departments
        self.departments = [
            "cardiology", "neurology", "orthopedics", "dermatology",
            "pediatrics", "gynecology", "ent", "ophthalmology",
            "general medicine", "general surgery", "dentistry",
            "radiology", "emergency medicine", "casualty"
        ]

        # Department routing map for symptoms / inquiries
        self.symptom_department_map = {
            "skin": "Dermatology",
            "rash": "Dermatology",
            "itching": "Dermatology",
            "acne": "Dermatology",
            "bone": "Orthopedics",
            "joint": "Orthopedics",
            "fracture": "Orthopedics",
            "knee": "Orthopedics",
            "spine": "Orthopedics",
            "back": "Orthopedics",
            "heart": "Cardiology",
            "blood pressure": "Cardiology",
            "hypertension": "Cardiology",
            "palpitation": "Cardiology",
            "eye": "Ophthalmology",
            "vision": "Ophthalmology",
            "cataract": "Ophthalmology",
            "child": "Pediatrics",
            "infant": "Pediatrics",
            "baby": "Pediatrics",
            "ear": "ENT",
            "nose": "ENT",
            "throat": "ENT",
            "sinus": "ENT",
            "hearing": "ENT",
            "brain": "Neurology",
            "nerve": "Neurology",
            "paralysis": "Neurology",
            "migraine": "Neurology",
            "pregnancy": "Gynecology",
            "menstrual": "Gynecology",
            "tooth": "Dentistry",
            "teeth": "Dentistry",
            "gum": "Dentistry",
            "fever": "General Medicine",
            "stomach": "General Medicine",
            "infection": "General Medicine"
        }

    def load_model(self):
        """Loads serialized model and vectorizer once at startup."""
        model_path = os.path.join(self.model_dir, "intent_model.joblib")
        vec_path = os.path.join(self.model_dir, "vectorizer.joblib")
        if os.path.exists(model_path) and os.path.exists(vec_path):
            try:
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vec_path)
                print(f"[OK] Hospital NLP Model and Vectorizer loaded successfully.")
            except Exception as e:
                print(f"[!] Error loading NLP model: {e}")
        else:
            print(f"[!] NLP model artifacts not found at {self.model_dir}. Please run train.py first.")

    def normalize_text(self, text: str) -> str:
        """Cleans and standardizes raw user message."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict_intent(self, text: str):
        """
        Classifies user intent and returns (intent, confidence).
        Falls back gracefully if confidence is below threshold.
        """
        cleaned = self.normalize_text(text)
        if not cleaned or not self.model or not self.vectorizer:
            return "unknown", 0.0

        # Safety & Emergency check first
        if detect_emergency(text):
            return "emergency", 1.0

        vec = self.vectorizer.transform([cleaned])
        probs = self.model.predict_proba(vec)[0]
        max_idx = probs.argmax()
        confidence = float(probs[max_idx])
        predicted_intent = self.model.classes_[max_idx]

        # Direct exact or high-priority rule boosts for common clinical queries (Rule Safety Layer)
        raw_lower = text.lower().strip()
        if any(g in raw_lower for g in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]):
            if "doctor" not in raw_lower and "department" not in raw_lower and "appointment" not in raw_lower and "emergency" not in raw_lower:
                return "greeting", 0.98
        if raw_lower in ["bye", "goodbye", "see you", "farewell"]:
            return "goodbye", 0.99
        if any(t in raw_lower for t in ["thanks", "thank you", "thank you so much", "many thanks"]):
            return "thanks", 0.99
        if "opd" in raw_lower and ("time" in raw_lower or "timing" in raw_lower or "hours" in raw_lower):
            return "opd_timings", 0.95
        if "book" in raw_lower and "appointment" in raw_lower:
            return "appointment_booking", 0.95
        if "department" in raw_lower and any(w in raw_lower for w in ["what", "which", "list", "show", "clinical", "have", "all"]):
            return "department_information", 0.92
        if "doctor" in raw_lower and any(w in raw_lower for w in ["who", "find", "list", "show", "specialist", "names"]):
            return "doctor_information", 0.92

        return predicted_intent, round(confidence, 4)

    def extract_entities(self, text: str) -> dict:
        """
        Extracts structured clinical entities: doctor names, departments,
        dates, times, and symptom keywords.
        """
        entities = {}
        text_lower = text.lower()

        # 1. Extract Doctor Name
        doc_pattern = re.search(r"\b(dr\.?|doctor)\s+([A-Za-z]+(\s+[A-Za-z]+)?)", text, re.IGNORECASE)
        if doc_pattern:
            entities["doctor"] = f"Dr. {doc_pattern.group(2).strip().title()}"

        # 2. Extract Department
        for dept in self.departments:
            if dept in text_lower:
                entities["department"] = dept.title()
                break

        # 3. Extract Dates
        today = datetime.now()
        if "tomorrow" in text_lower:
            target_date = today + timedelta(days=1)
            entities["date"] = target_date.strftime("%Y-%m-%d")
            entities["date_label"] = "Tomorrow"
        elif "today" in text_lower:
            entities["date"] = today.strftime("%Y-%m-%d")
            entities["date_label"] = "Today"
        else:
            # Check YYYY-MM-DD or DD/MM/YYYY
            iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
            if iso_match:
                entities["date"] = iso_match.group(1)
            else:
                slash_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
                if slash_match:
                    d, m, y = slash_match.groups()
                    entities["date"] = f"{y}-{int(m):02d}-{int(d):02d}"

        # 4. Extract Times
        time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", text, re.IGNORECASE)
        if time_match and any(marker in text_lower for marker in ["am", "pm", ":00", ":30"]):
            entities["time"] = time_match.group(1).strip()

        # 5. Extract Symptoms
        detected_symptoms = []
        for symptom in self.symptom_department_map.keys():
            if symptom in text_lower:
                detected_symptoms.append(symptom)
        if detected_symptoms:
            entities["symptoms"] = detected_symptoms

        # 6. Extract Appointment ID if present
        apt_match = re.search(r"\b(APT-[A-Z0-9-]+)\b", text, re.IGNORECASE)
        if apt_match:
            entities["appointment_id"] = apt_match.group(1).upper()

        return entities

    def update_context(self, session_id: str, new_entities: dict, intent: str):
        """Updates multi-turn conversation context for an active session."""
        if not session_id:
            return {}
        context = SESSION_CONTEXTS.get(session_id, {"step": "idle", "entities": {}, "last_intent": None})
        context["entities"].update(new_entities)
        context["last_intent"] = intent
        SESSION_CONTEXTS[session_id] = context
        return context

    def get_context(self, session_id: str):
        """Retrieves current session context."""
        return SESSION_CONTEXTS.get(session_id, {"step": "idle", "entities": {}, "last_intent": None})

    def clear_context(self, session_id: str):
        """Resets session context."""
        if session_id in SESSION_CONTEXTS:
            del SESSION_CONTEXTS[session_id]

# Singleton NLP instance
nlp_engine = HospitalNLP()
