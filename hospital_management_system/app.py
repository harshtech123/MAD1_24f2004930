#!/usr/bin/env python3
"""
Hospital Management System
Main Flask Application
"""

from app import create_app
from app.models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        from app.models import Admin
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                email='admin@hospital.com',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created - Username: admin, Password: admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)