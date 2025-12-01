"""
Patient Routes - Patient dashboard and appointment management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from app.models import db, Doctor, Patient, Department, Appointment, Treatment, DoctorAvailability

patient_bp = Blueprint('patient', __name__)

def patient_required(f):
    """Decorator to ensure only patients can access the route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.get_user_type() != 'patient':
            flash('Access denied. Patient privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    """Patient dashboard"""
    patient = current_user
    
    departments = Department.query.filter_by(is_active=True).all()
    
    today = datetime.today().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status == 'booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    recent_treatments = db.session.query(Treatment, Appointment, Doctor)\
        .join(Appointment, Treatment.appointment_id == Appointment.id)\
        .join(Doctor, Appointment.doctor_id == Doctor.id)\
        .filter(Appointment.patient_id == patient.id)\
        .order_by(Treatment.treatment_date.desc()).limit(5).all()
    
    current_date = datetime.today().date()
    
    total_appointments = Appointment.query.filter_by(patient_id=patient.id).count()
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id, status='completed'
    ).count()
    
    total_treatments = db.session.query(Treatment).join(Appointment).filter(
        Appointment.patient_id == patient.id
    ).count()
    
    doctors_count = db.session.query(Doctor.id).join(Appointment).filter(
        Appointment.patient_id == patient.id
    ).distinct().count()
    
    stats = {
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'upcoming_appointments': len(upcoming_appointments)
    }
    
    return render_template('patient/dashboard.html',
                         patient=patient,
                         current_date=current_date,
                         departments=departments,
                         upcoming_appointments=upcoming_appointments,
                         recent_treatments=recent_treatments,
                         total_appointments=total_appointments,
                         total_treatments=total_treatments,
                         doctors_count=doctors_count,
                         stats=stats)

@patient_bp.route('/doctors')
@login_required
@patient_required
def doctors():
    """View available doctors"""
    department_id = request.args.get('department')
    search_query = request.args.get('search', '').strip()
    
    query = Doctor.query.filter_by(is_active=True)
    
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    if search_query:
        query = query.filter(
            db.or_(
                Doctor.full_name.ilike(f'%{search_query}%'),
                Doctor.qualification.ilike(f'%{search_query}%')
            )
        )
    
    doctors = query.order_by(Doctor.full_name).all()
    departments = Department.query.filter_by(is_active=True).all()
    
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    
    doctor_availability = {}
    for doctor in doctors:
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.available_date >= today,
            DoctorAvailability.available_date <= next_week,
            DoctorAvailability.is_available == True
        ).order_by(DoctorAvailability.available_date).all()
        doctor_availability[doctor.id] = availability
    
    return render_template('patient/doctors.html',
                         doctors=doctors,
                         departments=departments,
                         doctor_availability=doctor_availability,
                         selected_department=department_id,
                         search_query=search_query)

@patient_bp.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment(doctor_id):
    """Book appointment with a doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if not doctor.is_active:
        flash('Doctor is not available for appointments', 'error')
        return redirect(url_for('patient.doctors'))
    
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')
        
        if not all([appointment_date, appointment_time]):
            flash('Please select date and time', 'error')
            return render_template('patient/book_appointment.html', doctor=doctor)
        
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            
            if date_obj < datetime.today().date():
                flash('Cannot book appointments for past dates', 'error')
                return render_template('patient/book_appointment.html', doctor=doctor)
            
            availability = DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.available_date == date_obj,
                DoctorAvailability.start_time <= time_obj,
                DoctorAvailability.end_time > time_obj,
                DoctorAvailability.is_available == True
            ).first()
            
            if not availability:
                flash('Doctor is not available at the selected time', 'error')
                return render_template('patient/book_appointment.html', doctor=doctor)
            
            existing_appointment = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == date_obj,
                Appointment.appointment_time == time_obj,
                Appointment.status == 'booked'
            ).first()
            
            if existing_appointment:
                flash('This time slot is already booked', 'error')
                return render_template('patient/book_appointment.html', doctor=doctor)
            
            appointment = Appointment(
                patient_id=current_user.id,
                doctor_id=doctor_id,
                appointment_date=date_obj,
                appointment_time=time_obj,
                reason=reason,
                status='booked'
            )
            
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('patient.appointments'))
            
        except ValueError:
            flash('Invalid date or time format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error booking appointment', 'error')
            print(f"Book appointment error: {e}")
    
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= next_week,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    departments = Department.query.filter_by(is_active=True).all()
    
    return render_template('patient/book_appointment.html', 
                         doctor=doctor, 
                         availability=availability,
                         departments=departments,
                         today=today)

@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    """View patient's appointments"""
    status_filter = request.args.get('status')
    
    query = Appointment.query.filter_by(patient_id=current_user.id)
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.appointment_time.desc()
    ).all()
    
    return render_template('patient/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter,
                         current_date=datetime.today().date())

@patient_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@patient_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'booked':
        flash('Only booked appointments can be cancelled', 'error')
        return redirect(url_for('patient.appointments'))
    
    appointment_datetime = datetime.combine(appointment.appointment_date, appointment.appointment_time)
    if appointment_datetime <= datetime.now() + timedelta(hours=2):
        flash('Cannot cancel appointments less than 2 hours before the scheduled time', 'error')
        return redirect(url_for('patient.appointments'))
    
    appointment.status = 'cancelled'
    appointment.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Appointment cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling appointment', 'error')
        print(f"Cancel appointment error: {e}")
    
    return redirect(url_for('patient.appointments'))

@patient_bp.route('/appointment/<int:appointment_id>/reschedule', methods=['GET', 'POST'])
@login_required
@patient_required
def reschedule_appointment(appointment_id):
    """Reschedule appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'booked':
        flash('Only booked appointments can be rescheduled', 'error')
        return redirect(url_for('patient.appointments'))
    
    if request.method == 'POST':
        new_date = request.form.get('appointment_date')
        new_time = request.form.get('appointment_time')
        
        if not all([new_date, new_time]):
            flash('Please select new date and time', 'error')
            today = datetime.today().date()
            next_week = today + timedelta(days=7)
            availability = DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == appointment.doctor_id,
                DoctorAvailability.available_date >= today,
                DoctorAvailability.available_date <= next_week,
                DoctorAvailability.is_available == True
            ).order_by(DoctorAvailability.available_date).all()
            return render_template('patient/reschedule_appointment.html', 
                                 appointment=appointment,
                                 availability=availability,
                                 current_date=datetime.today().date())
        
        try:
            date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(new_time, '%H:%M').time()
            
            if date_obj < datetime.today().date():
                flash('Cannot reschedule to past dates', 'error')
                today = datetime.today().date()
                next_week = today + timedelta(days=7)
                availability = DoctorAvailability.query.filter(
                    DoctorAvailability.doctor_id == appointment.doctor_id,
                    DoctorAvailability.available_date >= today,
                    DoctorAvailability.available_date <= next_week,
                    DoctorAvailability.is_available == True
                ).order_by(DoctorAvailability.available_date).all()
                return render_template('patient/reschedule_appointment.html', 
                                     appointment=appointment,
                                     availability=availability,
                                     current_date=datetime.today().date())
            
            availability = DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == appointment.doctor_id,
                DoctorAvailability.available_date == date_obj,
                DoctorAvailability.start_time <= time_obj,
                DoctorAvailability.end_time > time_obj,
                DoctorAvailability.is_available == True
            ).first()
            
            if not availability:
                flash('Doctor is not available at the selected time', 'error')
                today = datetime.today().date()
                next_week = today + timedelta(days=7)
                availability = DoctorAvailability.query.filter(
                    DoctorAvailability.doctor_id == appointment.doctor_id,
                    DoctorAvailability.available_date >= today,
                    DoctorAvailability.available_date <= next_week,
                    DoctorAvailability.is_available == True
                ).order_by(DoctorAvailability.available_date).all()
                return render_template('patient/reschedule_appointment.html', 
                                     appointment=appointment,
                                     availability=availability,
                                     current_date=datetime.today().date())
            
            existing_appointment = Appointment.query.filter(
                Appointment.doctor_id == appointment.doctor_id,
                Appointment.appointment_date == date_obj,
                Appointment.appointment_time == time_obj,
                Appointment.status == 'booked',
                Appointment.id != appointment_id
            ).first()
            
            if existing_appointment:
                flash('This time slot is already booked', 'error')
                today = datetime.today().date()
                next_week = today + timedelta(days=7)
                availability = DoctorAvailability.query.filter(
                    DoctorAvailability.doctor_id == appointment.doctor_id,
                    DoctorAvailability.available_date >= today,
                    DoctorAvailability.available_date <= next_week,
                    DoctorAvailability.is_available == True
                ).order_by(DoctorAvailability.available_date).all()
                return render_template('patient/reschedule_appointment.html', 
                                     appointment=appointment,
                                     availability=availability,
                                     current_date=datetime.today().date())
            
            appointment.appointment_date = date_obj
            appointment.appointment_time = time_obj
            appointment.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Appointment rescheduled successfully!', 'success')
            return redirect(url_for('patient.appointments'))
            
        except ValueError:
            flash('Invalid date or time format', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error rescheduling appointment', 'error')
            print(f"Reschedule appointment error: {e}")
    
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == appointment.doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= next_week,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    return render_template('patient/reschedule_appointment.html', 
                         appointment=appointment,
                         availability=availability,
                         current_date=datetime.today().date())

@patient_bp.route('/treatment_history')
@login_required
@patient_required
def treatment_history():
    """View patient's treatment history"""
    return redirect(url_for('patient.medical_records'))

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def profile():
    """Edit patient profile"""
    patient = current_user
    
    if request.method == 'POST':
        patient.full_name = request.form.get('full_name')
        patient.email = request.form.get('email')
        patient.phone = request.form.get('phone')
        patient.gender = request.form.get('gender')
        patient.address = request.form.get('address')
        patient.emergency_contact = request.form.get('emergency_contact')
        patient.blood_group = request.form.get('blood_group')
        patient.allergies = request.form.get('allergies')
        
        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('patient/profile.html', 
                                     patient=patient, 
                                     current_date=datetime.today().date())
            patient.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile', 'error')
            print(f"Update profile error: {e}")
    
    return render_template('patient/profile.html', 
                         patient=patient, 
                         current_date=datetime.today().date())

@patient_bp.route('/book_appointment')
@login_required  
@patient_required
def choose_doctor():
    """Show available doctors for booking appointment"""
    return redirect(url_for('patient.doctors'))

@patient_bp.route('/medical_records')
@login_required
@patient_required
def medical_records():
    """View patient's medical records"""
    patient = Patient.query.get(current_user.id)
    
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Treatment.treatment_date.desc()).all()
    
    return render_template('patient/medical_records.html', 
                         patient=patient, 
                         treatments=treatments,
                         current_date=datetime.today().date())

@patient_bp.route('/appointment/<int:appointment_id>/details')
@login_required
@patient_required
def appointment_details(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.filter_by(
        id=appointment_id, 
        patient_id=current_user.id
    ).first_or_404()
    
    return render_template('patient/appointment_details.html', 
                         appointment=appointment,
                         current_date=datetime.today().date())

@patient_bp.route('/api/doctors/<int:department_id>')
@login_required
@patient_required
def api_doctors_by_department(department_id):
    """Get doctors by department for AJAX requests"""
    doctors = Doctor.query.filter_by(
        department_id=department_id, 
        is_active=True
    ).all()
    
    return jsonify([{
        'id': doctor.id,
        'full_name': doctor.full_name,
        'specialization': doctor.specialization or 'General',
        'qualification': doctor.qualification,
        'experience_years': doctor.experience_years,
        'consultation_fee': doctor.consultation_fee
    } for doctor in doctors])

@patient_bp.route('/api/availability/<int:doctor_id>/<date>')
@login_required
@patient_required
def api_doctor_availability(doctor_id, date):
    """Get doctor availability for a specific date"""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.available_date == date_obj,
            DoctorAvailability.is_available == True
        ).all()
        
        return jsonify([{
            'id': avail.id,
            'start_time': avail.start_time.strftime('%H:%M'),
            'end_time': avail.end_time.strftime('%H:%M')
        } for avail in availability])
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400