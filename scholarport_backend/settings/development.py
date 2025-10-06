"""
Development settings - Debug enabled, permissive CORS, SQLite.
"""
from .base import *
import logging

# Debug mode
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Suppress Firebase warnings in development
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GLOG_minloglevel', '2')
logging.getLogger('google.auth.transport.grpc').setLevel(logging.ERROR)
logging.getLogger('google.auth._default').setLevel(logging.ERROR)

print("🔧 Development mode active - Debug ON, SQLite database")
