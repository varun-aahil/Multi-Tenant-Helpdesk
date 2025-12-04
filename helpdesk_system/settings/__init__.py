import os
from django.core.exceptions import ImproperlyConfigured

# Determine which settings to use
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'dev')

if ENVIRONMENT == 'prod':
    from .prod import *
elif ENVIRONMENT == 'dev':
    from .dev import *
else:
    from .base import *

