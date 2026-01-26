"""
Django settings for Scholarport Backend - University Search Chatbot
Production-ready configuration with PostgreSQL and proper security settings.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Suppress Google Cloud ALTS warnings
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GLOG_minloglevel', '2')

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Detect environment
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
IS_PRODUCTION = DJANGO_ENV == 'production'

if IS_PRODUCTION:
    print("Production mode active - Debug OFF, PostgreSQL database")
else:
    print("Development mode - Debug ON, SQLite database")

# SECRET KEY - Must be set in production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-neft+94-_5yu1nmh7wcfo#agm6^tp**k#%qf-(ep+ht_qzr^up')

# DEBUG - Off in production
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# ALLOWED HOSTS - Read from environment or use defaults
allowed_hosts_str = os.getenv('ALLOWED_HOSTS', '')
if allowed_hosts_str:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Add common production hosts
ALLOWED_HOSTS.extend(['chat.scholarport.co', 'api.scholarport.co', '65.1.127.116'])
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))  # Remove duplicates

# CSRF Trusted Origins for HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://chat.scholarport.co',
    'https://api.scholarport.co',
    'http://65.1.127.116',
    'http://localhost:3000',
]

# Security settings for production
if IS_PRODUCTION:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'

    # CSRF settings for Cloudflare Flexible SSL + Nginx
    CSRF_COOKIE_SECURE = False  # Set to False because nginx->backend is HTTP
    CSRF_COOKIE_HTTPONLY = False  # Allow JS to read for SPA
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to False because nginx->backend is HTTP
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_USE_SESSIONS = False  # Use cookie-based CSRF tokens


# Application definition
# These are all the apps (modules) that our Django project uses

INSTALLED_APPS = [
    # Default Django apps
    "django.contrib.admin",      # Admin interface for managing data
    "django.contrib.auth",       # User authentication system
    "django.contrib.contenttypes",  # Content type framework
    "django.contrib.sessions",   # Session framework
    "django.contrib.messages",   # Messaging framework
    "django.contrib.staticfiles", # Static file handling

    # Third-party apps
    "rest_framework",            # Django REST Framework for APIs
    "corsheaders",              # Handle Cross-Origin requests from frontend
    "drf_spectacular",          # OpenAPI 3.0 Schema Generation
    "drf_spectacular_sidecar",  # Serve Swagger UI and ReDoc static files

    # Our custom apps
    "chat",                     # Main chatbot functionality
    "monitoring",               # Slack notifications & health monitoring
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Enable CORS - must be first!
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "monitoring.middleware.RequestMonitoringMiddleware",  # Slack alerts for errors
]

ROOT_URLCONF = "scholarport_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "scholarport_backend.wsgi.application"


# Database Configuration
if IS_PRODUCTION:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'scholarport'),
            'USER': os.getenv('POSTGRES_USER', 'scholarport_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Django REST Framework configuration
# This configures our API settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # SessionAuthentication removed - enforces CSRF which breaks public APIs
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow all for now - will secure later
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # OpenAPI Schema Generation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# drf-spectacular settings for Swagger UI
SPECTACULAR_SETTINGS = {
    'TITLE': 'Scholarport API',
    'DESCRIPTION': '''
## Scholarport Backend API Documentation

A comprehensive API for university search chatbot functionality including:

- **Conversation Management**: Start and manage chatbot conversations
- **University Search**: Search and filter universities with recommendations
- **Admin Dashboard**: Analytics and data export for counselors
- **Firebase Integration**: Real-time data export capabilities

### Authentication
Most endpoints are publicly accessible. Admin endpoints will require authentication in future versions.

### Rate Limiting
No rate limiting is currently implemented.
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Chat', 'description': 'Conversation and message endpoints'},
        {'name': 'Universities', 'description': 'University search and details'},
        {'name': 'Admin', 'description': 'Admin dashboard and export endpoints'},
        {'name': 'Health', 'description': 'Health check endpoint'},
    ],
}

# CORS settings
cors_origins_str = os.getenv('CORS_ALLOWED_ORIGINS', '')
if cors_origins_str:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins_str.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]

CORS_ALLOWED_ORIGINS.extend([
    'https://chat.scholarport.co',
    'https://api.scholarport.co',
    'http://65.1.127.116',
])
CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS))

# Allow credentials in CORS requests
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    print("⚠️  Warning: OPENAI_API_KEY not set in .env file")

# Firebase Configuration (we'll set this up later)
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '')

# University Data File
UNIVERSITY_DATA_FILE = os.path.join(BASE_DIR, 'data.json')


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging for production
if IS_PRODUCTION:
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
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }

print(f"Loaded {'production' if IS_PRODUCTION else 'development'} settings")
print(f"Allowed hosts: {ALLOWED_HOSTS}")
