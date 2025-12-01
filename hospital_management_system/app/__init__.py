"""
Flask Application Factory and Configuration
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hospital-management-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Admin, Doctor, Patient
        user_type, user_id = user_id.split('_')
        if user_type == 'admin':
            return Admin.query.get(int(user_id))
        elif user_type == 'doctor':
            return Doctor.query.get(int(user_id))
        elif user_type == 'patient':
            return Patient.query.get(int(user_id))
        return None
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.doctor import doctor_bp
    from app.routes.patient import patient_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Add custom template filters
    @app.template_filter('age')
    def calculate_age(birth_date):
        """Calculate age from birth date"""
        if not birth_date:
            return None
        
        today = datetime.today().date()
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                return None
        elif hasattr(birth_date, 'date'):
            birth_date = birth_date.date()
            
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    
    return app