"""
URL configuration for helpdesk_system project.
"""
from django.contrib import admin
from django.urls import path, include
import logging

logger = logging.getLogger(__name__)

# Debug: Log URL patterns being loaded
try:
    from django_tenants.utils import get_tenant
    tenant = get_tenant()
    logger.warning(f'URLs loaded for tenant: {tenant.schema_name if tenant else "public"}')
except:
    logger.warning('URLs loaded (could not get tenant)')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tickets.urls')),
    path('api/', include('knowledgebase.urls')),
    path('api/', include('customers.urls')),
    path('', include('frontend.urls')),
]
