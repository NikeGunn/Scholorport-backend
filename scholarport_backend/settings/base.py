"""
Base settings shared across all environments.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Secret key - MUST be overridden in production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-changeme-in-production')

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "cloudinary_storage",
    "cloudinary",
    "chat",
    "booking",
    "blog",
    "partners",
    "contact",
    "admin_api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# drf-spectacular settings for Swagger UI
SPECTACULAR_SETTINGS = {
    'TITLE': 'Scholarport API',
    'DESCRIPTION': '''
## Scholarport Backend API Documentation

A comprehensive API for study abroad student counseling platform including:

### Core Features
- **Conversation Management**: AI-powered chatbot for university recommendations
- **University Search**: Search and filter universities with intelligent matching
- **Admin Dashboard**: Analytics and data export for counselors
- **Firebase Integration**: Real-time data export capabilities

### Booking System (NEW)
- **Counselor Profiles**: Browse available counselors and their specializations
- **Session Booking**: Book consultation sessions with counselors
- **Availability Management**: Manage counselor availability slots
- **Email Verification**: Secure booking confirmation via email

### Blog/Educational Content (NEW)
- **Articles & Guides**: Educational content about studying abroad
- **Categories & Tags**: Organized content for easy discovery
- **Comments**: Community engagement on posts
- **Media Library**: Image upload and management
- **Newsletter**: Email subscription for updates

### Authentication
Most endpoints are publicly accessible. Admin endpoints require authentication.
Booking uses email verification instead of user accounts.

### Image Storage
Images are stored using Cloudinary (cloud) or local storage (development).
    ''',
    'VERSION': '2.0.0',
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
        {'name': 'Booking', 'description': 'Session booking with counselors'},
        {'name': 'Counselors', 'description': 'Counselor profiles and availability'},
        {'name': 'Blog', 'description': 'Educational content and articles'},
        {'name': 'Blog Categories', 'description': 'Blog category management'},
        {'name': 'Blog Comments', 'description': 'Blog comments and discussions'},
        {'name': 'Partners', 'description': 'University and agent partners'},
        {'name': 'Contact', 'description': 'Contact form submissions'},
        {'name': 'Admin', 'description': 'Admin dashboard and export endpoints'},
        {'name': 'Admin Auth', 'description': 'Admin authentication (login, logout, profile)'},
        {'name': 'Admin Dashboard', 'description': 'Dashboard statistics and analytics'},
        {'name': 'Admin Users', 'description': 'Admin user management'},
        {'name': 'Admin Quick Actions', 'description': 'Quick actions and global search'},
        {'name': 'Admin - Partners', 'description': 'Partner management (admin only)'},
        {'name': 'Admin - Contact', 'description': 'Contact submissions management (admin only)'},
        {'name': 'Health', 'description': 'Health check endpoint'},
    ],
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudinary Configuration (for production image storage)
# Supports CLOUDINARY_URL format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
# Get your free API credentials at: https://cloudinary.com/
import cloudinary
import re

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')

if CLOUDINARY_URL:
    # Extract values from the URL
    # Format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    match = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', CLOUDINARY_URL)
    if match:
        CLOUDINARY_API_KEY = match.group(1)
        CLOUDINARY_API_SECRET = match.group(2)
        CLOUDINARY_CLOUD_NAME = match.group(3)

        # Configure cloudinary with explicit values (more reliable than cloudinary_url param)
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True
        )

        # Configure django-cloudinary-storage
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
            'API_KEY': CLOUDINARY_API_KEY,
            'API_SECRET': CLOUDINARY_API_SECRET,
        }
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
else:
    # Fallback to individual env vars
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

    if CLOUDINARY_CLOUD_NAME:
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True
        )
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
            'API_KEY': CLOUDINARY_API_KEY,
            'API_SECRET': CLOUDINARY_API_SECRET,
        }
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '')

# University Data File
UNIVERSITY_DATA_FILE = os.path.join(BASE_DIR, 'data.json')
