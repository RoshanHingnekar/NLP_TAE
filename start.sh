#!/bin/sh
set -e

echo "=== CareBridge Hospital Assistant Starting ==="

# Check and train NLP model if missing
if [ ! -f "backend/nlp/model/intent_model.joblib" ]; then
    echo "[*] Model artifacts not found. Training NLP intent classifier..."
    python backend/nlp/train.py
fi

# Seed database with initial departments, doctors, and demo users
echo "[*] Checking and seeding database records..."
python seed.py

# Start production WSGI Gunicorn server
PORT="${PORT:-5000}"
echo "[✓] Launching Gunicorn WSGI server on 0.0.0.0:${PORT}..."
exec gunicorn backend.app:app --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120 --access-logfile - --error-logfile -
