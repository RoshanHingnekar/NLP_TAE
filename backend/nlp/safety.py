"""
Medical Safety and Emergency Detection Layer
Ensures the assistant NEVER diagnoses, prescribes, or delays urgent medical care.
"""
import re

EMERGENCY_KEYWORDS = [
    r"\b(severe|sharp|crushing|tight|intense)?\s*chest pain\b",
    r"\bdifficulty breathing\b",
    r"\b(can'?t|cannot|unable to) breathe\b",
    r"\bshortness of breath\b",
    r"\bbreathless(ness)?\b",
    r"\bunconscious(ness)?\b",
    r"\bfainted\b|\bpassing out\b|\bloss of consciousness\b",
    r"\bheavy bleeding\b|\buncontrolled bleeding\b|\bhemorrhage\b",
    r"\bstroke\b|\bface drooping\b|\bspeech slurred\b|\barm weakness\b",
    r"\bsevere allergic reaction\b|\banaphylaxis\b",
    r"\bseizure(s)?\b|\bconvulsion(s)?\b|\bfits\b",
    r"\bpoison(ing|ed)?\b|\bswallowed poison\b|\btoxic chemical\b",
    r"\bsuicid(e|al|ing)?\b|\bkill myself\b|\bwant to die\b|\bend my life\b",
    r"\bsevere (head injury|burn|burns|trauma|bleeding|wound)\b",
    r"\bcoughing (up )?blood\b|\bvomiting blood\b",
    r"\bheart attack\b|\bcardiac arrest\b",
    r"\bparaly(sis|zed)\b"
]

EMERGENCY_REGEX = re.compile("|".join(EMERGENCY_KEYWORDS), re.IGNORECASE)

EMERGENCY_NOTICE_TEXT = (
    "⚠ EMERGENCY NOTICE\n"
    "This situation may require urgent medical attention. "
    "Please contact your local emergency services (Dial 112 / 911 / 102) "
    "or go to the nearest emergency department immediately.\n\n"
    "CareBridge Demo Hospital 24/7 Emergency Casualty: +1 (555) 019-9911.\n"
    "Do NOT rely on this chatbot for emergency or acute care."
)

GENERAL_MEDICAL_DISCLAIMER = (
    "\n\n[Medical Disclaimer: Hospital Assistant provides general information and administrative assistance only. "
    "It does not provide medical diagnosis or treatment. For medical concerns, consult a qualified healthcare professional.]"
)

# Safe educational responses for common symptom mentions
SYMPTOM_SAFE_GUIDES = {
    "headache": (
        "Headaches can have many possible causes, such as stress, dehydration, lack of sleep, eye strain, or sinus pressure. "
        "Resting in a quiet dark room and drinking adequate water may help mild cases. "
        "If headaches are persistent, severe, or accompanied by vision changes or fever, please consult our Neurology or General Medicine department."
    ),
    "fever": (
        "A fever is typically the body's natural defense against infection. "
        "Stay hydrated, rest adequately, and monitor your body temperature. "
        "If the fever exceeds 102°F (38.9°C), persists for more than 48 hours, or is accompanied by chills or stiffness, please see a doctor promptly."
    ),
    "cough": (
        "Cough and cold symptoms are commonly viral in origin. "
        "Warm fluids, steam inhalation, and throat lozenges often provide temporary relief. "
        "If you experience persistent cough beyond two weeks, wheezing, or high fever, an evaluation by our Pulmonology or ENT specialist is recommended."
    ),
    "stomach": (
        "Mild abdominal discomfort or indigestion is often linked to dietary changes, acidity, or minor gastric irritation. "
        "Eating light bland meals and avoiding oily food is generally suggested. "
        "If pain is sharp, persistent, localized to the lower right side, or accompanied by repeated vomiting, seek prompt medical care."
    ),
    "skin": (
        "Skin rashes, dryness, or itching can occur due to allergies, dermatitis, eczema, or contact irritants. "
        "Keep the area clean, avoid scratching, and do not apply unknown steroid creams without prescription. "
        "We recommend scheduling a consultation with our Dermatology department."
    ),
    "joint": (
        "Joint and muscle aches may arise from strain, posture, physical exertion, or arthritis. "
        "Gentle stretching, rest, and warm/cold compresses may help mild discomfort. "
        "For prolonged joint swelling, stiffness, or mobility issues, our Orthopedics department is available to assist."
    ),
    "eye": (
        "Eye irritation or redness could be due to strain, dust, dryness, or conjunctivitis. "
        "Avoid rubbing your eyes and take frequent screen breaks. "
        "If there is pain, sudden vision change, or discharge, consult our Ophthalmology department immediately."
    )
}

def detect_emergency(text: str) -> bool:
    """
    Check if the user input contains high-risk emergency expressions.
    Returns True if an emergency is detected.
    """
    if not text:
        return False
    return bool(EMERGENCY_REGEX.search(text))

def get_emergency_response() -> str:
    """Return prominent urgent emergency safety notice."""
    return EMERGENCY_NOTICE_TEXT

def get_safe_symptom_guidance(text: str) -> str:
    """
    Provide non-prescriptive, educational health guidance with mandatory medical disclaimers.
    Never prescribes medicines, dosage, or claims diagnosis.
    """
    text_lower = text.lower()
    for keyword, guidance in SYMPTOM_SAFE_GUIDES.items():
        if keyword in text_lower:
            return guidance + GENERAL_MEDICAL_DISCLAIMER

    # Fallback safe guidance
    return (
        "Symptoms can have a wide variety of underlying causes. "
        "While mild symptoms often resolve with rest and proper hydration, any symptoms that cause discomfort, "
        "worsen over time, or recur should be evaluated in person by a qualified doctor.\n\n"
        "Would you like me to help you book an appointment with our General Medicine department?"
        + GENERAL_MEDICAL_DISCLAIMER
    )

def sanitize_response(response: str, is_health_related: bool = False) -> str:
    """
    Attach standard medical disclaimer if response discusses health or symptoms.
    """
    if is_health_related and GENERAL_MEDICAL_DISCLAIMER not in response:
        return response + GENERAL_MEDICAL_DISCLAIMER
    return response
