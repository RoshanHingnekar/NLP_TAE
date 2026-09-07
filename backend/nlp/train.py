"""
NLP Intent Classifier Training Script
Trains a TF-IDF Vectorizer + Logistic Regression classifier on intents.json
Saves the trained artifacts into backend/nlp/model/
"""
import os
import json
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
INTENTS_PATH = os.path.join(CURRENT_DIR, "intents.json")
MODEL_DIR = os.path.join(CURRENT_DIR, "model")

def clean_text(text: str) -> str:
    """Normalize text: lowercase, strip, remove special characters."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def train_intent_model(intents_file=INTENTS_PATH, output_dir=MODEL_DIR):
    """
    Load intents, extract features with TF-IDF, train Logistic Regression,
    and persist artifacts.
    """
    print(f"[*] Loading intents dataset from: {intents_file}")
    with open(intents_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = []
    labels = []

    for item in data.get("intents", []):
        intent = item["intent"]
        for example in item.get("examples", []):
            cleaned = clean_text(example)
            if cleaned:
                texts.append(cleaned)
                labels.append(intent)

    print(f"[*] Total training utterances loaded: {len(texts)} across {len(set(labels))} intents.")

    # Stratified Train-Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )

    print(f"[*] Training samples: {len(X_train)} | Test samples: {len(X_test)}")

    # TF-IDF Feature Extraction with unigrams and bigrams
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        stop_words="english"
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Multi-class Logistic Regression with balanced tuning
    classifier = LogisticRegression(
        max_iter=2000,
        C=10.0,
        solver="lbfgs",
        random_state=42
    )
    classifier.fit(X_train_vec, y_train)

    # Evaluation
    train_preds = classifier.predict(X_train_vec)
    test_preds = classifier.predict(X_test_vec)

    train_acc = accuracy_score(y_train, train_preds)
    test_acc = accuracy_score(y_test, test_preds)

    print(f"[OK] Train Accuracy: {train_acc * 100:.2f}%")
    print(f"[OK] Test Accuracy:  {test_acc * 100:.2f}%")
    print("\n--- Test Classification Report ---")
    print(classification_report(y_test, test_preds, zero_division=0))

    # Persist model and vectorizer
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "intent_model.joblib")
    vectorizer_path = os.path.join(output_dir, "vectorizer.joblib")

    joblib.dump(classifier, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    print(f"[OK] Model successfully saved to: {model_path}")
    print(f"[OK] Vectorizer successfully saved to: {vectorizer_path}")

    return {
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "classes": list(classifier.classes_)
    }

if __name__ == "__main__":
    train_intent_model()
