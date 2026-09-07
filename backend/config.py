import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "carebridge-hospital-assistant-secret-key-2025")
    
    # Database URL handling
    # Render provides postgres:// which SQLAlchemy 1.4+ expects as postgresql://
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url:
        if raw_db_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = raw_db_url.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        # Fallback to local SQLite file for development
        db_path = os.path.join(BASE_DIR, "hospital.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    } if "postgresql" in SQLALCHEMY_DATABASE_URI else {}

    # JWT Settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # CORS configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Environment
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

    # NLP Settings
    NLP_CONFIDENCE_THRESHOLD = float(os.environ.get("NLP_CONFIDENCE_THRESHOLD", "0.55"))
    NLP_MODEL_DIR = os.path.join(BASE_DIR, "nlp", "model")

    # Frontend directory
    FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


class ProductionConfig(Config):
    """Production configuration."""
    ENVIRONMENT = "production"
    # Ensure DATABASE_URL is explicitly provided in production


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENVIRONMENT = "development"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ENVIRONMENT = "testing"
    NLP_CONFIDENCE_THRESHOLD = 0.50


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}

def get_config():
    env = os.environ.get("ENVIRONMENT", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
