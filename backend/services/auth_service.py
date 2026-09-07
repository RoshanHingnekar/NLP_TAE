"""
Authentication and Authorization Service
Provides secure password hashing, JWT generation/verification, and role checks.
"""
from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from backend.models import User
from backend.database import db

def hash_password(password: str) -> str:
    """Securely hash a password using scrypt / pbkdf2."""
    return generate_password_hash(password, method="scrypt")

def verify_password(password: str, hashed_password: str) -> bool:
    """Check a cleartext password against a hash."""
    return check_password_hash(hashed_password, password)

def create_access_token(user: User) -> str:
    """Generate a signed JWT token containing user identity and role."""
    secret = current_app.config["JWT_SECRET_KEY"]
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_access_token(token: str):
    """Decode and validate a JWT access token."""
    secret = current_app.config["JWT_SECRET_KEY"]
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user_from_token():
    """Extract current user from Bearer Authorization header, or None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    return db.session.get(User, user_id)

def token_required(f):
    """Decorator ensuring a valid JWT is presented."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_token()
        if not user:
            return jsonify({
                "error": "Authentication required",
                "message": "Valid authorization token missing or expired. Please login."
            }), 401
        return f(user, *args, **kwargs)
    return decorated

def roles_required(*allowed_roles):
    """Decorator restricting endpoint access to specific roles (e.g. 'admin', 'staff')."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user_from_token()
            if not user:
                return jsonify({
                    "error": "Authentication required",
                    "message": "Valid authorization token missing or expired."
                }), 401
            if user.role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
                }), 403
            return f(user, *args, **kwargs)
        return decorated
    return decorator

def register_user(name, email, password, phone="", role="patient"):
    """Validates and registers a new user."""
    email = email.strip().lower()
    if not email or not password or not name:
        return None, "Name, email, and password are required."
    
    # Check existing email
    if User.query.filter_by(email=email).first():
        return None, "An account with this email address already exists."

    # Validate role
    if role not in ["patient", "staff", "admin"]:
        role = "patient"

    new_user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        phone=phone.strip() if phone else None,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user, None

def authenticate_user(email, password):
    """Authenticates credentials and returns (user, token, error)."""
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return None, None, "Invalid email or password."

    token = create_access_token(user)
    return user, token, None
