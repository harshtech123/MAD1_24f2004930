"""
Authentication Routes - Login, Logout, Registration
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Admin, Doctor, Patient

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Universal login page for all user types"""
    if current_user.is_authenticated:
        user_type = current_user.get_user_type()
        if user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user_type == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif user_type == 'patient':
            return redirect(url_for('patient.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if not username or not password or not user_type:
            flash('Please fill in all fields', 'error')
            return render_template('auth/login.html')
        
        user = None
        if user_type == 'admin':
            user = Admin.query.filter_by(username=username).first()
        elif user_type == 'doctor':
            user = Doctor.query.filter_by(username=username).first()
        elif user_type == 'patient':
            user = Patient.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            
            if not next_page:
                if user_type == 'admin':
                    next_page = url_for('admin.dashboard')
                elif user_type == 'doctor':
                    next_page = url_for('doctor.dashboard')
                elif user_type == 'patient':
                    next_page = url_for('patient.dashboard')
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid credentials or account is inactive', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        address = request.form.get('address')
        emergency_contact = request.form.get('emergency_contact')
        blood_group = request.form.get('blood_group')
        allergies = request.form.get('allergies')
        
        if not all([username, email, full_name, password, confirm_password]):
            flash('Please fill in all required fields', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register.html')
        
        if Patient.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if Patient.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html')
        
        from datetime import datetime
        patient = Patient(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            gender=gender,
            address=address,
            emergency_contact=emergency_contact,
            blood_group=blood_group,
            allergies=allergies
        )
        
        if date_of_birth:
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        patient.set_password(password)
        
        try:
            db.session.add(patient)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout current user"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))