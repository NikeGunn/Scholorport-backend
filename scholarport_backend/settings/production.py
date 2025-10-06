"""
Production settings - Debug OFF, PostgreSQL, strict security.
"""
from .base import *
import logging

# Security settings
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production!")

# Allowed hosts - restrict to your domain
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database - PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'scholarport'),
        'USER': os.getenv('POSTGRES_USER', 'scholarport_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# CORS - Now handled by Nginx
# Django CORS middleware not needed since Nginx adds headers
# But keeping these for documentation/fallback
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# Security middleware - SSL disabled for initial deployment
SECURE_SSL_REDIRECT = False  # Disabled - no SSL certificates yet
SESSION_COOKIE_SECURE = False  # Disabled - no HTTPS
CSRF_COOKIE_SECURE = False  # Disabled - no HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security) - Disabled until SSL is set up
SECURE_HSTS_SECONDS = 0  # Disabled
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Proxy settings for Nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging - Create logs directory if it doesn't exist
LOG_DIR = '/app/logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': f'{LOG_DIR}/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Suppress Firebase warnings
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GLOG_minloglevel', '2')
logging.getLogger('google.auth.transport.grpc').setLevel(logging.ERROR)
logging.getLogger('google.auth._default').setLevel(logging.ERROR)

print("🔒 Production mode active - Debug OFF, PostgreSQL database")
