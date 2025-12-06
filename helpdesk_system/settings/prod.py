"""
Production settings
"""
from .base import *
import os

DEBUG = False

# Get ALLOWED_HOSTS from environment, but also auto-detect from Render
allowed_hosts = env.list('ALLOWED_HOSTS', default=[])
# Auto-detect Render domain if available
render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_hostname and render_hostname not in allowed_hosts:
    allowed_hosts.append(render_hostname)
# Also check for any .onrender.com domains in the environment
for key, value in os.environ.items():
    if 'onrender.com' in str(value) and value not in allowed_hosts:
        allowed_hosts.append(value)
ALLOWED_HOSTS = allowed_hosts if allowed_hosts else ['*']  # Fallback to * if empty

# Security settings for production
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging for production
# In containerized environments, logs should go to stdout/stderr
# so they can be captured by the platform (Render, Railway, etc.)
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
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'frontend.middleware': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'helpdesk_system.urls': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'frontend.middleware_debug': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

