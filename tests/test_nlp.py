"""
NLP Pipeline and Medical Safety Unit Tests
"""
import pytest
from backend.nlp.chatbot import nlp_engine
from backend.nlp.safety import detect_emergency, get_emergency_response

def test_greeting_intent():
    intent, conf = nlp_engine.predict_intent("Hello assistant, good morning")
    assert intent == "greeting"
    assert conf >= 0.55

def test_doctor_query_intent():
    intent, conf = nlp_engine.predict_intent("Who are your doctors in cardiology?")
    assert intent in ["doctor_information", "department_information"]
    assert conf >= 0.50

def test_department_query_intent():
    intent, conf = nlp_engine.predict_intent("What clinical departments do you have?")
    assert intent == "department_information"
    assert conf >= 0.55

def test_appointment_booking_intent():
    intent, conf = nlp_engine.predict_intent("I want to book an appointment with a doctor")
    assert intent == "appointment_booking"
    assert conf >= 0.55

def test_opd_timings_intent():
    intent, conf = nlp_engine.predict_intent("What are the OPD timings?")
    assert intent == "opd_timings"
    assert conf >= 0.55

def test_faq_intent():
    intent, conf = nlp_engine.predict_intent("Can you answer some frequently asked questions?")
    assert intent == "faq"
    assert conf >= 0.50

def test_emergency_detection():
    # Test emergency phrase triggers
    assert detect_emergency("I have severe chest pain and cannot breathe") is True
    assert detect_emergency("Patient is unconscious and bleeding heavily") is True
    assert detect_emergency("Someone drank poison and had a seizure") is True
    assert detect_emergency("What are the OPD timings?") is False

    # Emergency intent override
    intent, conf = nlp_engine.predict_intent("I have severe chest pain and feel faint")
    assert intent == "emergency"
    assert conf == 1.0

def test_entity_extraction():
    entities = nlp_engine.extract_entities("I want to book an appointment with Dr Sharma in Cardiology tomorrow at 10:00 am")
    assert "doctor" in entities
    assert "Sharma" in entities["doctor"]
    assert "department" in entities
    assert entities["department"] == "Cardiology"
    assert "date" in entities
    assert "time" in entities
    assert "10:00" in entities["time"]

def test_confidence_threshold():
    intent, conf = nlp_engine.predict_intent("Random gibberish asdfghjkl xyz")
    assert conf < 0.60 or intent == "unknown"
