"""
Database Models for Hospital Management System
"""

from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"admin_{self.id}"
    
    def get_user_type(self):
        return 'admin'

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True)

class Doctor(UserMixin, db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    qualification = db.Column(db.String(255))
    specialization = db.Column(db.String(100))  # Doctor's specialization
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    consultation_fee = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"doctor_{self.id}"
    
    def get_user_type(self):
        return 'doctor'
    
    def get_today_appointments(self):
        today = date.today()
        return Appointment.query.filter(
            Appointment.doctor_id == self.id,
            db.func.date(Appointment.appointment_date) == today
        ).order_by(Appointment.appointment_time).all()
    
    def get_week_appointments(self):
        today = date.today()
        week_end = today + timedelta(days=7)
        return Appointment.query.filter(
            Appointment.doctor_id == self.id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= week_end
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

class Patient(UserMixin, db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    allergies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"patient_{self.id}"
    
    def get_user_type(self):
        return 'patient'
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    reason = db.Column(db.Text)
    appointment_type = db.Column(db.String(50), default='consultation')  # consultation, follow_up, check_up, procedure, emergency
    priority = db.Column(db.String(20), default='routine')  # routine, urgent, emergency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')
    
    @property
    def is_past_due(self):
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        return appointment_datetime < datetime.now()

class Treatment(db.Model):
    __tablename__ = 'treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    treatment_date = db.Column(db.DateTime, default=datetime.utcnow)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    
    def get_patient(self):
        return Patient.query.get(self.appointment.patient_id)
    
    def get_doctor(self):
        return Doctor.query.get(self.appointment.doctor_id)