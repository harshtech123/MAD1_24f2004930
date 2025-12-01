"""
Admin Routes - Admin dashboard and management functions
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from app.models import db, Admin, Doctor, Patient, Department, Appointment, Treatment

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure only admins can access the route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.get_user_type() != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    total_patients = Patient.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    
    today = date.today()
    today_appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).count()
    
    pending_appointments = Appointment.query.filter_by(status='booked').count()
    completed_appointments = Appointment.query.filter_by(status='completed').count()
    
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(10).all()
    
    departments = db.session.query(
        Department, 
        db.func.count(Doctor.id).label('doctor_count')
    ).outerjoin(Doctor, (Doctor.department_id == Department.id) & (Doctor.is_active == True))\
    .group_by(Department.id).all()
    
    stats = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_appointments=recent_appointments,
                         departments=departments)

@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    """Manage doctors"""
    search_query = request.args.get('search', '').strip()
    department_id = request.args.get('department')
    
    query = Doctor.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Doctor.full_name.ilike(f'%{search_query}%'),
                Doctor.email.ilike(f'%{search_query}%'),
                Doctor.license_number.ilike(f'%{search_query}%')
            )
        )
    
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    doctors = query.order_by(Doctor.full_name).all()
    departments = Department.query.filter_by(is_active=True).all()
    
    return render_template('admin/doctors.html', 
                         doctors=doctors, 
                         departments=departments,
                         search_query=search_query,
                         selected_department=department_id)

@admin_bp.route('/doctor/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    """Add new doctor"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')
        department_id = request.form.get('department_id')
        experience_years = request.form.get('experience_years', 0)
        qualification = request.form.get('qualification')
        consultation_fee = request.form.get('consultation_fee', 0)
        password = request.form.get('password')
        
        if not all([username, email, full_name, license_number, department_id, password]):
            flash('Please fill in all required fields', 'error')
            departments = Department.query.filter_by(is_active=True).all()
            return render_template('admin/add_doctor.html', departments=departments)
        
        if Doctor.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            departments = Department.query.filter_by(is_active=True).all()
            return render_template('admin/add_doctor.html', departments=departments)
        
        if Doctor.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            departments = Department.query.filter_by(is_active=True).all()
            return render_template('admin/add_doctor.html', departments=departments)
        
        if Doctor.query.filter_by(license_number=license_number).first():
            flash('License number already exists', 'error')
            departments = Department.query.filter_by(is_active=True).all()
            return render_template('admin/add_doctor.html', departments=departments)
        
        doctor = Doctor(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            license_number=license_number,
            department_id=int(department_id),
            experience_years=int(experience_years) if experience_years else 0,
            qualification=qualification,
            consultation_fee=float(consultation_fee) if consultation_fee else 0.0
        )
        doctor.set_password(password)
        
        try:
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('admin.doctors'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding doctor. Please try again.', 'error')
            print(f"Add doctor error: {e}")
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('admin/add_doctor.html', departments=departments)

@admin_bp.route('/doctor/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    """Edit doctor details"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        doctor.username = request.form.get('username')
        doctor.email = request.form.get('email')
        doctor.full_name = request.form.get('full_name')
        doctor.phone = request.form.get('phone')
        doctor.license_number = request.form.get('license_number')
        doctor.department_id = int(request.form.get('department_id'))
        doctor.experience_years = int(request.form.get('experience_years', 0))
        doctor.qualification = request.form.get('qualification')
        doctor.consultation_fee = float(request.form.get('consultation_fee', 0))
        
        new_password = request.form.get('password')
        if new_password:
            doctor.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Doctor updated successfully!', 'success')
            return redirect(url_for('admin.doctors'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating doctor. Please try again.', 'error')
            print(f"Edit doctor error: {e}")
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('admin/edit_doctor.html', doctor=doctor, departments=departments)

@admin_bp.route('/doctor/<int:doctor_id>/toggle_status')
@login_required
@admin_required
def toggle_doctor_status(doctor_id):
    """Activate/Deactivate doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = not doctor.is_active
    
    try:
        db.session.commit()
        status = "activated" if doctor.is_active else "deactivated"
        flash(f'Doctor {doctor.full_name} has been {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating doctor status', 'error')
        print(f"Toggle doctor status error: {e}")
    
    return redirect(url_for('admin.doctors'))

@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    """Manage patients"""
    search_query = request.args.get('search', '').strip()
    
    query = Patient.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Patient.full_name.ilike(f'%{search_query}%'),
                Patient.email.ilike(f'%{search_query}%'),
                Patient.phone.ilike(f'%{search_query}%')
            )
        )
    
    patients = query.order_by(Patient.full_name).all()
    
    return render_template('admin/patients.html', 
                         patients=patients,
                         search_query=search_query)

@admin_bp.route('/patient/<int:patient_id>/toggle_status')
@login_required
@admin_required
def toggle_patient_status(patient_id):
    """Activate/Deactivate patient"""
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = not patient.is_active
    
    try:
        db.session.commit()
        status = "activated" if patient.is_active else "deactivated"
        flash(f'Patient {patient.full_name} has been {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating patient status', 'error')
        print(f"Toggle patient status error: {e}")
    
    return redirect(url_for('admin.patients'))

@admin_bp.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_patient(patient_id):
    """Edit patient information"""
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        patient.full_name = request.form.get('full_name')
        patient.email = request.form.get('email')
        patient.phone = request.form.get('phone')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        patient.emergency_contact = request.form.get('emergency_contact')
        patient.allergies = request.form.get('allergies')
        patient.medical_history = request.form.get('medical_history')
        
        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        new_password = request.form.get('password')
        if new_password:
            patient.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Patient information updated successfully!', 'success')
            return redirect(url_for('admin.patients'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating patient information. Please try again.', 'error')
            print(f"Edit patient error: {e}")
    
    return render_template('admin/edit_patient.html', patient=patient)

@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    """View all appointments"""
    status_filter = request.args.get('status')
    date_filter = request.args.get('date')
    
    query = Appointment.query
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Appointment.appointment_date) == filter_date)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    current_date = date.today()
    
    return render_template('admin/appointments.html', 
                         appointments=appointments,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         current_date=current_date)

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    """Manage departments"""
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/department/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    """Add new department"""
    name = request.form.get('name')
    description = request.form.get('description')
    is_active = request.form.get('is_active') == 'on'
    
    if not name:
        flash('Department name is required', 'error')
        return redirect(url_for('admin.departments'))
    
    if Department.query.filter_by(name=name).first():
        flash('Department already exists', 'error')
        return redirect(url_for('admin.departments'))
    
    department = Department(name=name, description=description, is_active=is_active)
    
    try:
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding department', 'error')
        print(f"Add department error: {e}")
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/department/<int:department_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_department(department_id):
    """Edit department details"""
    department = Department.query.get_or_404(department_id)
    
    department.name = request.form.get('name')
    department.description = request.form.get('description')
    department.is_active = request.form.get('is_active') == 'on'
    
    try:
        db.session.commit()
        flash('Department updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating department', 'error')
        print(f"Edit department error: {e}")
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/department/<int:department_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_department_status(department_id):
    """Toggle department status"""
    department = Department.query.get_or_404(department_id)
    department.is_active = not department.is_active
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Toggle department status error: {e}")
        return jsonify({'success': False})

@admin_bp.route('/patient/add', methods=['POST'])
@login_required
@admin_required
def add_patient():
    """Add new patient"""
    username = request.form.get('username')
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    password = request.form.get('password')
    date_of_birth = request.form.get('date_of_birth')
    gender = request.form.get('gender')
    blood_group = request.form.get('blood_group')
    address = request.form.get('address')
    emergency_contact = request.form.get('emergency_contact')
    
    if not all([username, email, full_name, password]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('admin.patients'))
    
    if Patient.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin.patients'))
    
    if Patient.query.filter_by(email=email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('admin.patients'))
    
    patient = Patient(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        gender=gender,
        blood_group=blood_group,
        address=address,
        emergency_contact=emergency_contact
    )
    
    if date_of_birth:
        patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    
    patient.set_password(password)
    
    try:
        db.session.add(patient)
        db.session.commit()
        flash('Patient registered successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error registering patient. Please try again.', 'error')
        print(f"Add patient error: {e}")
    
    return redirect(url_for('admin.patients'))

@admin_bp.route('/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required
@admin_required
def update_appointment_status(appointment_id):
    """Update appointment status"""
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json()
    
    appointment.status = data.get('status')
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Update appointment status error: {e}")
        return jsonify({'success': False})