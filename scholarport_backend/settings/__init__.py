"""
Settings package initialization.
Imports the appropriate settings based on DJANGO_ENV environment variable.
"""
import os

ENV = os.getenv('DJANGO_ENV', 'development')

if ENV == 'production':
    from .production import *
elif ENV == 'staging':
    from .staging import *
else:
    from .development import *

print(f"🔧 Loaded {ENV} settings")
