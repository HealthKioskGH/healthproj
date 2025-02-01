# HealthKiosk - Modern Healthcare Management Platform

## Overview
HealthKiosk is a comprehensive healthcare management platform that facilitates seamless interactions between patients and healthcare providers. The platform offers a modern, secure, and user-friendly interface for managing medical appointments, health records, and doctor-patient communications.

## Features

### For Patients
- **Appointment Management**
  - Book new appointments
  - View upcoming and past appointments
  - Cancel or reschedule appointments
  - Receive appointment reminders

- **Health Records**
  - Track vital signs
  - Record symptoms
  - Maintain health profile
  - Access medical history

- **Doctor Interaction**
  - Choose primary care physician
  - Direct messaging with doctors
  - View doctor profiles and specializations
  - Receive medical updates and notifications

### For Doctors
- **Patient Management**
  - View patient appointments
  - Access patient health records
  - Monitor patient vital signs
  - Add medical notes and prescriptions

- **Schedule Management**
  - Set availability hours
  - Manage appointment slots
  - Handle appointment requests
  - Set up recurring schedules

- **Health Monitoring**
  - Track patient progress
  - Set up monitoring alerts
  - Record patient vitals
  - Document medical conditions

### System Features
- Real-time notifications
- Secure data encryption
- Role-based access control
- Interactive dashboards
- Responsive design
- Session management
- Audit logging

## Technical Stack

### Backend
- Python 3.8+
- Django 4.2
- Django REST Framework
- SQLite (default database)

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Font Awesome icons

### Security Features
- CSRF protection
- Session security
- Password hashing
- Secure cookie handling
- XSS prevention

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/healthkiosk.git
cd healthkiosk
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Project Structure
```
healthkiosk/
├── accounts/            # User authentication and management
├── appointments/        # Appointment handling
├── doctors/            # Doctor-specific functionality
├── patients/           # Patient-specific functionality
├── notifications/      # Notification system
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── healthproj/         # Project settings
└── manage.py           # Django management script
```

## Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

### Database Configuration
The default configuration uses SQLite. For production, it's recommended to use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## API Documentation

### Authentication Endpoints
- POST `/api/accounts/register/` - Register new user
- POST `/api/accounts/login/` - Login user
- POST `/api/accounts/logout/` - Logout user

### Patient Endpoints
- GET/POST `/api/patients/vitals/` - Manage vital signs
- GET/POST `/api/patients/records/` - Access medical records
- GET/POST `/api/patients/symptoms/` - Log symptoms
- GET/POST `/api/patients/profiles/` - Manage health profiles

### Doctor Endpoints
- GET/POST `/api/doctors/notes/` - Manage patient notes
- GET/POST `/api/doctors/monitoring/` - Patient monitoring
- GET/POST `/api/doctors/alerts/` - Health alerts

### Appointment Endpoints
- GET/POST `/api/appointments/appointments/` - Manage appointments
- GET/POST `/api/appointments/schedules/` - Doctor schedules
- GET/POST `/api/appointments/timeslots/` - Available time slots

## Security Considerations

1. **Data Protection**
   - All sensitive data is encrypted at rest
   - Secure transmission using HTTPS
   - Regular security audits
   - Compliance with healthcare data regulations

2. **Access Control**
   - Role-based access control
   - Session timeout after inactivity
   - IP-based access restrictions
   - Two-factor authentication support

3. **Monitoring**
   - Activity logging
   - Error tracking
   - Performance monitoring
   - Security alert system

## Testing

Run the test suite:
```bash
python manage.py test
```

Run with coverage:
```bash
coverage run manage.py test
coverage report
```

## Deployment

### Prerequisites
- Python 3.8+
- PostgreSQL
- Redis (for caching)
- Nginx
- Gunicorn

### Deployment Steps
1. Set up a production server
2. Configure Nginx as reverse proxy
3. Set up SSL certificates
4. Configure Gunicorn
5. Set up environment variables
6. Deploy using your preferred method (e.g., Docker, manual deployment)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request


## Support

For support, please email support@healthkiosk.com or create an issue in the repository.

## Authors

- Initial work - Mohammed Ibrahim
- See also the list of contributors who participated in this project.

## Acknowledgments

- Thanks to all contributors who have helped shape HealthKiosk
- Special thanks to Emmanuella for assigning this project to me
- Inspired by modern healthcare needs and digital transformation

---
 