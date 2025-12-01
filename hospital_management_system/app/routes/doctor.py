"""
Doctor Routes - Doctor dashboard and patient management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from app.models import db, Doctor, Patient, Appointment, Treatment, DoctorAvailability

doctor_bp = Blueprint('doctor', __name__)

def doctor_required(f):
    """Decorator to ensure only doctors can access the route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.get_user_type() != 'doctor':
            flash('Access denied. Doctor privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Doctor dashboard"""
    doctor = current_user
    current_date = date.today()
    
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == current_date
    ).all()
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date > current_date,
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date.asc()).limit(5).all()
    
    total_patients = db.session.query(Patient.id).join(Appointment).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().count()
    
    pending_appointments_list = Appointment.query.filter_by(
        doctor_id=doctor.id, status='pending'
    ).all()
    
    recent_treatments = Treatment.query.join(Appointment).filter(
        Appointment.doctor_id == doctor.id
    ).order_by(Treatment.treatment_date.desc()).limit(5).all()
    
    today_appointments_count = len(today_appointments)
    total_patients_count = total_patients
    pending_appointments_count = len(pending_appointments_list)
    
    start_of_month = current_date.replace(day=1)
    month_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= start_of_month
    ).all()
    month_appointments_count = len(month_appointments)
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         current_date=current_date,
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         total_patients=total_patients,
                         pending_appointments=pending_appointments_list,
                         recent_treatments=recent_treatments,
                         today_appointments_count=today_appointments_count,
                         total_patients_count=total_patients_count,
                         pending_appointments_count=pending_appointments_count,
                         month_appointments_count=month_appointments_count)

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    """View doctor's appointments"""
    status_filter = request.args.get('status')
    date_filter = request.args.get('date')
    
    query = Appointment.query.filter_by(doctor_id=current_user.id)
    
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
    today_count = sum(1 for apt in appointments if apt.appointment_date == current_date)
    scheduled_count = sum(1 for apt in appointments if apt.status in ['scheduled', 'confirmed', 'pending', 'booked'])
    completed_count = sum(1 for apt in appointments if apt.status == 'completed')
    cancelled_count = sum(1 for apt in appointments if apt.status == 'cancelled')
    
    return render_template('doctor/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         current_date=current_date,
                         today_count=today_count,
                         scheduled_count=scheduled_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count)

@doctor_bp.route('/appointment/<int:appointment_id>/complete', methods=['GET', 'POST'])
@login_required
@doctor_required
def complete_appointment(appointment_id):
    """Mark appointment as completed and add treatment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('doctor.appointments'))
    
    if appointment.status not in ['scheduled', 'confirmed', 'pending', 'booked']:
        flash('Only scheduled, confirmed, pending, or booked appointments can be marked as completed', 'error')
        return redirect(url_for('doctor.appointments'))
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        follow_up_required = 'follow_up_required' in request.form
        follow_up_date = request.form.get('follow_up_date')
        
        if not diagnosis:
            flash('Diagnosis is required', 'error')
            return render_template('doctor/complete_appointment.html', 
                                 appointment=appointment,
                                 current_date=date.today())
        
        treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            follow_up_required=follow_up_required
        )
        
        if follow_up_date and follow_up_required:
            treatment.follow_up_date = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
        
        appointment.status = 'completed'
        appointment.updated_at = datetime.utcnow()
        
        try:
            db.session.add(treatment)
            db.session.commit()
            flash('Appointment completed successfully!', 'success')
            return redirect(url_for('doctor.appointments'))
        except Exception as e:
            db.session.rollback()
            flash('Error completing appointment', 'error')
            print(f"Complete appointment error: {e}")
    
    return render_template('doctor/complete_appointment.html', 
                         appointment=appointment,
                         current_date=date.today())

@doctor_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@doctor_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('doctor.appointments'))
    
    if appointment.status not in ['scheduled', 'confirmed', 'pending', 'booked']:
        flash('Only scheduled, confirmed, pending, or booked appointments can be cancelled', 'error')
        return redirect(url_for('doctor.appointments'))
    
    appointment.status = 'cancelled'
    appointment.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Appointment cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling appointment', 'error')
        print(f"Cancel appointment error: {e}")
    
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/patients')
@login_required
@doctor_required
def patients():
    """View doctor's patients"""
    patients = db.session.query(Patient).join(Appointment)\
        .filter(Appointment.doctor_id == current_user.id)\
        .distinct(Patient.id).all()
    
    return render_template('doctor/patients.html', patients=patients)

@doctor_bp.route('/patient/<int:patient_id>/history')
@login_required
@doctor_required
def patient_history(patient_id):
    """View patient's treatment history with this doctor"""
    patient = Patient.query.get_or_404(patient_id)
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    if not appointments:
        flash('No appointment history found with this patient', 'error')
        return redirect(url_for('doctor.patients'))
    
    return render_template('doctor/patient_history.html', 
                         patient=patient, 
                         appointments=appointments)

@doctor_bp.route('/availability')
@login_required
@doctor_required
def availability():
    """Manage doctor availability"""
    today = date.today()
    next_week = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == current_user.id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= next_week
    ).order_by(DoctorAvailability.available_date).all()
    
    return render_template('doctor/availability.html', availability=availability)

@doctor_bp.route('/availability/add', methods=['POST'])
@login_required
@doctor_required
def add_availability():
    """Add availability slot"""
    available_date = request.form.get('available_date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not all([available_date, start_time, end_time]):
        flash('All fields are required', 'error')
        return redirect(url_for('doctor.availability'))
    
    try:
        date_obj = datetime.strptime(available_date, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        
        if start_time_obj >= end_time_obj:
            flash('End time must be after start time', 'error')
            return redirect(url_for('doctor.availability'))
        
        if date_obj < date.today():
            flash('Cannot add availability for past dates', 'error')
            return redirect(url_for('doctor.availability'))
        
    except ValueError:
        flash('Invalid date or time format', 'error')
        return redirect(url_for('doctor.availability'))
    
    existing = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == current_user.id,
        DoctorAvailability.available_date == date_obj,
        db.or_(
            db.and_(
                DoctorAvailability.start_time <= start_time_obj,
                DoctorAvailability.end_time > start_time_obj
            ),
            db.and_(
                DoctorAvailability.start_time < end_time_obj,
                DoctorAvailability.end_time >= end_time_obj
            )
        )
    ).first()
    
    if existing:
        flash('Availability slot overlaps with existing slot', 'error')
        return redirect(url_for('doctor.availability'))
    
    availability = DoctorAvailability(
        doctor_id=current_user.id,
        available_date=date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj
    )
    
    try:
        db.session.add(availability)
        db.session.commit()
        flash('Availability added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding availability', 'error')
        print(f"Add availability error: {e}")
    
    return redirect(url_for('doctor.availability'))

@doctor_bp.route('/availability/<int:availability_id>/delete', methods=['POST'])
@login_required
@doctor_required
def delete_availability(availability_id):
    """Delete availability slot"""
    availability = DoctorAvailability.query.get_or_404(availability_id)
    
    if availability.doctor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('doctor.availability'))
    
    try:
        db.session.delete(availability)
        db.session.commit()
        flash('Availability deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting availability', 'error')
        print(f"Delete availability error: {e}")
    
    return redirect(url_for('doctor.availability'))

@doctor_bp.route('/treatments')
@login_required
@doctor_required
def treatments():
    """View treatments created by the doctor"""
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.id
    ).order_by(Treatment.treatment_date.desc()).all()
    
    current_date = date.today()
    
    return render_template('doctor/treatments.html', 
                         treatments=treatments,
                         current_date=current_date)

@doctor_bp.route('/appointment/<int:appointment_id>/details')
@login_required
@doctor_required
def appointment_details(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.filter_by(
        id=appointment_id, 
        doctor_id=current_user.id
    ).first_or_404()
    
    return render_template('doctor/appointment_details.html', appointment=appointment)

@doctor_bp.route('/patient/<int:patient_id>/details')
@login_required
@doctor_required
def patient_details(patient_id):
    """View patient details"""
    patient = Patient.query.get_or_404(patient_id)
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).all()
    
    if not appointments:
        flash('You can only view details of your own patients', 'error')
        return redirect(url_for('doctor.patients'))
    
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == current_user.id
    ).order_by(Treatment.treatment_date.desc()).all()
    
    current_date = date.today()
    return render_template('doctor/patient_details.html', 
                         patient=patient, 
                         appointments=appointments,
                         treatments=treatments,
                         current_date=current_date)

@doctor_bp.route('/appointment/<int:appointment_id>/confirm')
@login_required
@doctor_required
def confirm_appointment(appointment_id):
    """Confirm an appointment"""
    appointment = Appointment.query.filter_by(
        id=appointment_id, 
        doctor_id=current_user.id
    ).first_or_404()
    
    appointment.status = 'confirmed'
    
    try:
        db.session.commit()
        flash('Appointment confirmed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error confirming appointment', 'error')
    
    return redirect(url_for('doctor.appointments'))

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@doctor_required
def profile():
    """View and update doctor profile"""
    doctor = current_user
    
    if request.method == 'POST':
        doctor.full_name = request.form.get('full_name', doctor.full_name)
        doctor.phone = request.form.get('phone', doctor.phone)
        doctor.qualification = request.form.get('qualification', doctor.qualification)
        doctor.specialization = request.form.get('specialization', doctor.specialization)
        doctor.experience_years = int(request.form.get('experience_years', doctor.experience_years))
        doctor.consultation_fee = float(request.form.get('consultation_fee', doctor.consultation_fee))
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('doctor/profile.html', doctor=doctor)
            doctor.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('doctor.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile', 'error')
            print(f"Profile update error: {e}")
    
    return render_template('doctor/profile.html', doctor=doctor)