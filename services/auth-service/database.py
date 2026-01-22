"""
Shared Database Module for Auth Service
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        try:
            # Use inspect to check existing tables before creating
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'users' not in existing_tables:
                db.create_all()
                print("Auth Service: Database tables created")
            else:
                print("Auth Service: Tables already exist, skipping creation")
            
            # Create admin user if not exists
            admin_username = app.config.get('ADMIN_USERNAME', 'admin')
            admin = User.query.filter_by(username=admin_username).first()
            if not admin:
                admin = User(
                    username=admin_username,
                    email=app.config.get('ADMIN_EMAIL', 'admin@genovaai.com'),
                    is_admin=True,
                    is_active=True
                )
                admin.set_password(app.config.get('ADMIN_PASSWORD', 'admin123'))
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user '{admin_username}' created")
        except Exception as e:
            print(f"Auth Service: Database init warning: {e}")
