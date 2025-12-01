"""
API Routes - RESTful API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.models import db, Doctor, Patient, Department, Appointment, Treatment, DoctorAvailability

api_bp = Blueprint('api', __name__)

@api_bp.route('/departments', methods=['GET'])
@login_required
def get_departments():
    """Get all departments"""
    departments = Department.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': dept.id,
        'name': dept.name,
        'description': dept.description
    } for dept in departments])

@api_bp.route('/doctors', methods=['GET'])
@login_required
def get_doctors():
    """Get doctors with optional filtering"""
    department_id = request.args.get('department_id')
    search = request.args.get('search', '').strip()
    
    query = Doctor.query.filter_by(is_active=True)
    
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    if search:
        query = query.filter(
            db.or_(
                Doctor.full_name.ilike(f'%{search}%'),
                Doctor.qualification.ilike(f'%{search}%')
            )
        )
    
    doctors = query.all()
    
    return jsonify([{
        'id': doctor.id,
        'full_name': doctor.full_name,
        'qualification': doctor.qualification,
        'experience_years': doctor.experience_years,
        'consultation_fee': doctor.consultation_fee,
        'department': doctor.department.name,
        'department_id': doctor.department_id
    } for doctor in doctors])

@api_bp.route('/doctor/<int:doctor_id>/availability', methods=['GET'])
@login_required
def get_doctor_availability(doctor_id):
    """Get doctor's availability for the next 7 days"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    today = date.today()
    next_week = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date >= today,
        DoctorAvailability.available_date <= next_week,
        DoctorAvailability.is_available == True
    ).order_by(DoctorAvailability.available_date).all()
    
    return jsonify([{
        'id': avail.id,
        'date': avail.available_date.isoformat(),
        'start_time': avail.start_time.strftime('%H:%M'),
        'end_time': avail.end_time.strftime('%H:%M')
    } for avail in availability])

@api_bp.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    """Get user's appointments or create new appointment"""
    
    if request.method == 'GET':
        user_type = current_user.get_user_type()
        status = request.args.get('status')
        date_filter = request.args.get('date')
        
        if user_type == 'patient':
            query = Appointment.query.filter_by(patient_id=current_user.id)
        elif user_type == 'doctor':
            query = Appointment.query.filter_by(doctor_id=current_user.id)
        elif user_type == 'admin':
            query = Appointment.query
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if status:
            query = query.filter(Appointment.status == status)
        
        if date_filter:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Appointment.appointment_date) == filter_date)
        
        appointments = query.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        result = []
        for appointment in appointments:
            result.append({
                'id': appointment.id,
                'patient_name': appointment.patient.full_name,
                'doctor_name': appointment.doctor.full_name,
                'department': appointment.doctor.department.name,
                'date': appointment.appointment_date.isoformat(),
                'time': appointment.appointment_time.strftime('%H:%M'),
                'status': appointment.status,
                'reason': appointment.reason,
                'created_at': appointment.created_at.isoformat()
            })
        
        return jsonify(result)
    
    elif request.method == 'POST':
        if current_user.get_user_type() != 'patient':
            return jsonify({'error': 'Only patients can book appointments'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        doctor_id = data.get('doctor_id')
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        reason = data.get('reason')
        
        if not all([doctor_id, appointment_date, appointment_time]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            doctor = Doctor.query.get(doctor_id)
            if not doctor or not doctor.is_active:
                return jsonify({'error': 'Invalid or inactive doctor'}), 400
            
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            
            if date_obj < date.today():
                return jsonify({'error': 'Cannot book appointments for past dates'}), 400
            
            availability = DoctorAvailability.query.filter(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.available_date == date_obj,
                DoctorAvailability.start_time <= time_obj,
                DoctorAvailability.end_time > time_obj,
                DoctorAvailability.is_available == True
            ).first()
            
            if not availability:
                return jsonify({'error': 'Doctor not available at selected time'}), 400
            
            existing = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == date_obj,
                Appointment.appointment_time == time_obj,
                Appointment.status == 'booked'
            ).first()
            
            if existing:
                return jsonify({'error': 'Time slot already booked'}), 400
            
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
            
            return jsonify({
                'message': 'Appointment booked successfully',
                'appointment_id': appointment.id
            }), 201
            
        except ValueError:
            return jsonify({'error': 'Invalid date or time format'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to book appointment'}), 500

@api_bp.route('/appointment/<int:appointment_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def appointment_detail(appointment_id):
    """Get, update, or delete specific appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    user_type = current_user.get_user_type()
    
    if user_type == 'patient' and appointment.patient_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    elif user_type == 'doctor' and appointment.doctor_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    elif user_type not in ['admin', 'doctor', 'patient']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        return jsonify({
            'id': appointment.id,
            'patient_name': appointment.patient.full_name,
            'doctor_name': appointment.doctor.full_name,
            'department': appointment.doctor.department.name,
            'date': appointment.appointment_date.isoformat(),
            'time': appointment.appointment_time.strftime('%H:%M'),
            'status': appointment.status,
            'reason': appointment.reason,
            'created_at': appointment.created_at.isoformat()
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'status' in data and user_type in ['doctor', 'admin']:
            new_status = data['status']
            if new_status in ['completed', 'cancelled'] and appointment.status == 'booked':
                appointment.status = new_status
                appointment.updated_at = datetime.utcnow()
        
        if 'reason' in data and user_type in ['patient', 'admin']:
            appointment.reason = data['reason']
        
        try:
            db.session.commit()
            return jsonify({'message': 'Appointment updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update appointment'}), 500
    
    elif request.method == 'DELETE':
        if appointment.status == 'booked':
            appointment.status = 'cancelled'
            appointment.updated_at = datetime.utcnow()
            
            try:
                db.session.commit()
                return jsonify({'message': 'Appointment cancelled successfully'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': 'Failed to cancel appointment'}), 500
        else:
            return jsonify({'error': 'Only booked appointments can be cancelled'}), 400

@api_bp.route('/patients', methods=['GET'])
@login_required
def get_patients():
    """Get patients (for doctors and admins)"""
    user_type = current_user.get_user_type()
    
    if user_type not in ['doctor', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    search = request.args.get('search', '').strip()
    
    if user_type == 'doctor':
        query = db.session.query(Patient).join(Appointment)\
            .filter(Appointment.doctor_id == current_user.id)\
            .distinct(Patient.id)
    else:
        query = Patient.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Patient.full_name.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%')
            )
        )
    
    patients = query.all()
    
    return jsonify([{
        'id': patient.id,
        'full_name': patient.full_name,
        'email': patient.email,
        'phone': patient.phone,
        'age': patient.age,
        'gender': patient.gender,
        'blood_group': patient.blood_group
    } for patient in patients])

@api_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get system statistics (admin only)"""
    if current_user.get_user_type() != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    stats = {
        'total_patients': Patient.query.filter_by(is_active=True).count(),
        'total_doctors': Doctor.query.filter_by(is_active=True).count(),
        'total_departments': Department.query.filter_by(is_active=True).count(),
        'total_appointments': Appointment.query.count(),
        'booked_appointments': Appointment.query.filter_by(status='booked').count(),
        'completed_appointments': Appointment.query.filter_by(status='completed').count(),
        'cancelled_appointments': Appointment.query.filter_by(status='cancelled').count()
    }
    
    today = date.today()
    stats['today_appointments'] = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).count()
    
    return jsonify(stats)

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500