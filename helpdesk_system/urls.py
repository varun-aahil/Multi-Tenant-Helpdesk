"""
URL configuration for helpdesk_system project.
"""
from django.contrib import admin
from django.urls import path, include
import logging

logger = logging.getLogger(__name__)

# Debug: Log URL patterns being loaded (this happens at import time, before tenant routing)
logger.warning('URL patterns being loaded (import time)')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tickets.urls')),
    path('api/', include('knowledgebase.urls')),
    path('api/', include('customers.urls')),
    path('', include('frontend.urls')),
]

# Debug: Log that URL patterns are configured
logger.warning(f'URL patterns configured: {len(urlpatterns)} patterns')
