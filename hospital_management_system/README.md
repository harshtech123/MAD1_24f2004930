# Hospital Management System

A comprehensive web-based Hospital Management System built with Flask, SQLite, Bootstrap, and Jinja2 templating.

## Features

### Admin Features
- **Dashboard**: Complete overview of hospital statistics
- **Doctor Management**: Add, edit, deactivate doctors
- **Patient Management**: View and manage patient records
- **Appointment Management**: View all appointments across the system
- **Department Management**: Create and manage hospital departments
- **Search Functionality**: Search doctors and patients by various criteria

### Doctor Features
- **Dashboard**: View today's and weekly appointments
- **Patient Management**: View assigned patients and their history
- **Appointment Handling**: Mark appointments as completed or cancelled
- **Treatment Records**: Add diagnosis, prescriptions, and notes
- **Availability Management**: Set availability for the next 7 days

### Patient Features
- **Registration & Login**: Secure patient registration system
- **Find Doctors**: Search doctors by department and specialization
- **Appointment Booking**: Book appointments with available doctors
- **Appointment Management**: View, reschedule, or cancel appointments
- **Treatment History**: Access complete medical records and prescriptions
- **Profile Management**: Update personal information

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (lightweight, serverless database)
- **Frontend**: Bootstrap 5 (responsive UI framework)
- **Templating**: Jinja2 (Flask's templating engine)
- **Authentication**: Flask-Login (user session management)
- **Icons**: Font Awesome
- **Charts**: Chart.js (for dashboard analytics)

## Project Structure

```
hospital_management_system/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   ├── admin.py            # Admin routes
│   │   ├── doctor.py           # Doctor routes
│   │   ├── patient.py          # Patient routes
│   │   ├── main.py             # Main/landing routes
│   │   └── api.py              # RESTful API routes
│   ├── templates/
│   │   ├── base.html           # Base template
│   │   ├── index.html          # Landing page
│   │   ├── auth/               # Authentication templates
│   │   ├── admin/              # Admin templates
│   │   ├── doctor/             # Doctor templates
│   │   └── patient/            # Patient templates
│   └── static/
│       ├── css/
│       │   └── style.css       # Custom styles
│       └── js/
│           └── main.js         # Custom JavaScript
├── app.py                      # Main application file
├── setup_data.py               # Initial data setup script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Download
Download the project files to your local machine.

### Step 2: Install Dependencies
```bash
cd hospital_management_system
pip install -r requirements.txt
```

### Step 3: Set Up Initial Data
```bash
python setup_data.py
```

### Step 4: Run the Application
```bash
python app.py
```

The application will be available at: **http://localhost:5000**

## Default Login Credentials

### Admin Access
- **Username**: `admin`
- **Password**: `admin123`

### Doctor Access
- **Usernames**: `dr_smith`, `dr_johnson`, `dr_brown`, `dr_davis`
- **Password**: `doctor123`

### Patient Access
- **Usernames**: `patient1`, `patient2`, `patient3`
- **Password**: `patient123`

## Core Functionalities

### Authentication System
- Role-based access control (Admin, Doctor, Patient)
- Secure password hashing using Werkzeug
- Session management with Flask-Login
- Protected routes with login requirements

### Database Models
- **Admin**: System administrators
- **Doctor**: Medical professionals with specializations
- **Patient**: Individuals seeking medical care
- **Department**: Medical specializations/departments
- **Appointment**: Scheduled consultations
- **Treatment**: Medical records and prescriptions
- **DoctorAvailability**: Doctor scheduling system

### Key Features Implementation

#### Appointment System
- Prevents double-booking at same time slots
- Real-time availability checking
- Status tracking (Booked → Completed → Cancelled)
- 2-hour minimum cancellation policy

#### Search Functionality
- Admin: Search doctors by name, specialization, license
- Admin: Search patients by name, email, phone
- Patient: Search doctors by name and qualification
- Department-based filtering

#### Treatment Records
- Complete patient history tracking
- Diagnosis and prescription management
- Doctor notes and follow-up recommendations
- Patient access to own medical records

## API Endpoints

The system includes RESTful API endpoints:

- `GET /api/departments` - List all departments
- `GET /api/doctors` - List doctors with filtering options
- `GET /api/appointments` - User-specific appointments
- `POST /api/appointments` - Book new appointment
- `PUT /api/appointment/<id>` - Update appointment
- `DELETE /api/appointment/<id>` - Cancel appointment
- `GET /api/statistics` - System statistics (admin only)

## Security Features

- Password complexity requirements
- Input validation and sanitization
- SQL injection prevention through SQLAlchemy ORM
- XSS protection through Jinja2 auto-escaping
- CSRF protection considerations
- Role-based access control

## Browser Compatibility

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (responsive design)

## Development Notes

### Database
- Uses SQLite for development (can be easily changed to PostgreSQL/MySQL for production)
- Database file: `hospital.db` (created automatically)
- Foreign key constraints ensure data integrity

### Styling
- Bootstrap 5 for responsive layout
- Custom CSS for hospital-specific theming
- Font Awesome icons throughout the interface
- Consistent color scheme and typography

### JavaScript
- Vanilla JavaScript (no framework dependencies)
- Form validation and user experience enhancements
- AJAX functionality for dynamic content
- Chart.js integration for analytics

## Future Enhancements

- Email notifications for appointments
- SMS reminders
- Payment integration
- Medical report file uploads
- Advanced reporting and analytics
- Multi-language support
- Mobile app development

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed using `pip install -r requirements.txt`

2. **Database Issues**: Delete the `hospital.db` file and run `python setup_data.py` again

3. **Port Already in Use**: Change the port in `app.py` from 5000 to another port (e.g., 8000)

4. **Permission Issues**: Make sure you have write permissions in the project directory

## Support

For issues or questions about the Hospital Management System, please check:

1. Ensure all dependencies are properly installed
2. Verify Python version compatibility
3. Check that the database is properly initialized
4. Review the console output for error messages

## License

This project is developed for educational purposes as part of the MAD1 course requirements.

---

**Hospital Management System v1.0**  
*Efficient Healthcare Management Solution*