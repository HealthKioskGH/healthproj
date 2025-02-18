from .base import *
import dj_database_url

DEBUG = False

# Get secret key from environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Allow Heroku subdomain and your custom domain
ALLOWED_HOSTS = [
    '.herokuapp.com',  # Allows all Heroku subdomains
    'yourdomain.com',  # Your custom domain if you have one
]

# Configure Database using Heroku DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,  # Keep connection alive for 10 minutes
        ssl_require=True   # Require SSL for database connection
    )
}

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - Write to stdout/stderr for Heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Email settings (using Heroku SendGrid add-on)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('SENDGRID_SERVER', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('SENDGRID_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # This stays as 'apikey' for SendGrid
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL') 