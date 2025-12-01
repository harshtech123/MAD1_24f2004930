#!/usr/bin/env python3
"""
Hospital Management System - Simple Database Initialization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = None
try:
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.models import db, Admin, Doctor, Patient, Department, Appointment, DoctorAvailability
        from datetime import datetime, date, time, timedelta
        
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created!")
        
        # Create admin user
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                email='admin@hospital.com',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print(" Admin user created!")
        
        # Create departments
        departments_data = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular care'},
            {'name': 'Neurology', 'description': 'Brain and nervous system'},
            {'name': 'Orthopedics', 'description': 'Bones and joints'},
            {'name': 'Pediatrics', 'description': 'Children healthcare'},
            {'name': 'General Medicine', 'description': 'General medical care'}
        ]
        
        for dept_data in departments_data:
            if not Department.query.filter_by(name=dept_data['name']).first():
                department = Department(**dept_data)
                db.session.add(department)
        
        db.session.commit()
        print(" Departments created!")
        
        # Create sample doctors
        if Doctor.query.count() == 0:
            departments = Department.query.all()
            if departments:
                doctor_data = {
                    'username': 'dr_smith',
                    'email': 'dr.smith@hospital.com',
                    'full_name': 'Dr. John Smith',
                    'phone': '+1-555-0101',
                    'license_number': 'LIC001',
                    'experience_years': 10,
                    'qualification': 'MD, MBBS',
                    'specialization': 'Cardiology',
                    'department_id': departments[0].id,
                    'consultation_fee': 150.00
                }
                doctor = Doctor(**doctor_data)
                doctor.set_password('doctor123')
                db.session.add(doctor)
                db.session.commit()
                print(" Sample doctor created!")
        
        # Create sample patient
        if Patient.query.count() == 0:
            patient_data = {
                'username': 'patient1',
                'email': 'patient1@email.com',
                'full_name': 'Alice Wilson',
                'phone': '+1-555-1001',
                'date_of_birth': date(1990, 5, 15),
                'gender': 'Female',
                'blood_group': 'A+',
                'address': '123 Main St, City'
            }
            patient = Patient(**patient_data)
            patient.set_password('patient123')
            db.session.add(patient)
            db.session.commit()
            print(" Sample patient created!")
        
        print("\n Database setup completed successfully!")
        print("=" * 50)
        print("Admin Login: admin / admin123")
        print("Doctor Login: dr_smith / doctor123") 
        print("Patient Login: patient1 / patient123")
        print("=" * 50)
        print("\nTo start the application, run:")
        print("source venv/bin/activate && python3 app.py")

except Exception as e:
    print(f" Error: {e}")
    import traceback
    traceback.print_exc()