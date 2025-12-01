"""
Main Routes - Landing page and general routes
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        user_type = current_user.get_user_type()
        if user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user_type == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif user_type == 'patient':
            return redirect(url_for('patient.dashboard'))
    
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')