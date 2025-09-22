"""
Django settings for Scholarport Backend - University Search Chatbot

This file contains all the configuration for our Django application.
As a beginner, each setting is explained to help you understand what it does.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Suppress Google Cloud ALTS warnings in development
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GLOG_minloglevel', '2')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# In production, this should be a long, random string
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-neft+94-_5yu1nmh7wcfo#agm6^tp**k#%qf-(ep+ht_qzr^up')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Hosts that can access our application
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


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

    # Our custom apps
    "chat",                     # Main chatbot functionality
    "admin_panel",              # Admin features for counselors
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


# Database
# For development, we use SQLite (simple file-based database)
# For production, you would use PostgreSQL

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
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow all for now - will secure later
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings for frontend integration
# This allows our React frontend to communicate with our Django backend
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5000',
]

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
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
