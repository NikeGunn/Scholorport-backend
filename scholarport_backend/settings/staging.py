"""
Staging settings - Similar to production but with debug logging.
"""
from .production import *

# Allow slightly more permissive settings for staging
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Logging with more verbosity
LOGGING['root']['level'] = 'DEBUG'

print("🔧 Staging mode active - PostgreSQL database, Debug logging")
