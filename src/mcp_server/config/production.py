"""
Production configuration for MCP Test Generator
"""
import os
from datetime import timedelta

# Security settings
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
PERMANENT_SESSION_LIFETIME = timedelta(days=1)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Rate limiting
RATELIMIT_DEFAULT = "100/hour"
RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Sentry configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'production')

# Metrics
ENABLE_METRICS = True
METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))

# Cache configuration
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = os.getenv('REDIS_URL')
CACHE_DEFAULT_TIMEOUT = 300

# TestRail configuration
TESTRAIL_SECTION_ID = int(os.getenv('TESTRAIL_SECTION_ID', '1'))
TESTRAIL_PROJECT_ID = int(os.getenv('TESTRAIL_PROJECT_ID', '1'))

# Webhook configuration
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
WEBHOOK_TIMEOUT = 30  # seconds 