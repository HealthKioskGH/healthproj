# HealthKiosk - Healthcare Management System

## Overview
HealthKiosk is a Django-based healthcare management system that facilitates patient-doctor interactions, appointment scheduling, and medical record management. The system features a custom user authentication system that differentiates between patients and doctors.

## Technical Stack

### Backend
- Python 3.9.21
- Django 4.2.7
- PostgreSQL (via dj-database-url)
- Django REST Framework 3.14.0

### Additional Packages
- django-allauth: For authentication
- django-jazzmin: For admin interface
- whitenoise: For static file handling
- sendgrid: For email services
- Pillow: For image handling

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd healthkiosk
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Environment Variables
Create a `.env` file with:
```
DATABASE_URL=your-database-url
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST_USER=healthkioskgh@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

4. Database Setup:
```bash
python manage.py migrate
python manage.py createsuperuser
```

## Deployment to Heroku

1. Create Heroku app:
```bash
heroku create healthkiosk
```

2. Add PostgreSQL:
```bash
heroku addons:create heroku-postgresql:mini
```

3. Configure environment:
```bash
heroku config:set DJANGO_SETTINGS_MODULE=healthproj.settings
heroku config:set SECRET_KEY=your-secret-key
```

4. Deploy:
```bash
git push heroku main
```

5. Run migrations:
```bash
heroku run python manage.py migrate
```

## Project Structure

### Key Files
- `healthproj/settings.py`: Main settings file
- `accounts/models.py`: Custom user model
- `accounts/migrations/`: Database migrations for user model

### Custom User Model
The system uses a custom user model (`accounts.User`) that includes:
- User type (patient/doctor)
- Profile information
- Doctor-specific fields
- Patient-doctor relationships

## Development Notes

### Database Migrations
When modifying the User model:
1. Make changes to `accounts/models.py`
2. Create migrations:
```bash
python manage.py makemigrations accounts
```
3. Apply migrations:
```bash
python manage.py migrate
```

### Common Issues
- If you encounter migration issues, try:
```bash
heroku pg:reset DATABASE
heroku run python manage.py migrate
```

### Authentication
- The system uses both Django's built-in auth and django-allauth
- Email verification is optional but enabled
- Session timeout is set to 1 hour

## Security Features
- CSRF protection enabled
- Secure cookie settings
- WhiteNoise for static file serving
- Email verification support
- Session management with timeout

## Contributing
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Environment Setup
Required environment variables:
- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

## Support
For issues or questions, create a GitHub issue or contact the development team.

---

Last updated: March 2024
 