"""
URL configuration for helpdesk_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

# Debug: Log URL patterns being loaded (this happens at import time, before tenant routing)
logger.warning('URL patterns being loaded (import time)')

def debug_test_view(request):
    """Simple test view to verify URL routing works"""
    try:
        from django_tenants.utils import get_tenant
        tenant = get_tenant()
        tenant_info = f"Tenant: {tenant.schema_name if tenant else 'public'}"
    except Exception as e:
        tenant_info = f"Could not get tenant: {e}"
    
    return HttpResponse(f"Debug Test View - {tenant_info} - Path: {request.path}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tickets.urls')),
    path('api/', include('knowledgebase.urls')),
    path('api/', include('customers.urls')),
    path('debug-test/', debug_test_view, name='debug_test'),  # Test route
    path('', include('frontend.urls')),
]

# Debug: Log that URL patterns are configured
logger.warning(f'URL patterns configured: {len(urlpatterns)} patterns')
