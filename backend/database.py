from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask application."""
    db.init_app(app)
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
