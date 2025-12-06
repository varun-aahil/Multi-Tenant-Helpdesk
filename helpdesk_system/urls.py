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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.warning(f'[debug_test_view] VIEW CALLED! Path: {request.path}')
    logger.warning(f'[debug_test_view] Host: {request.get_host()}')
    
    try:
        from django_tenants.utils import get_tenant
        tenant = get_tenant(request)
        tenant_info = f"Tenant: {tenant.schema_name if tenant else 'public'}"
        logger.warning(f'[debug_test_view] {tenant_info}')
    except Exception as e:
        tenant_info = f"Could not get tenant: {e}"
        logger.warning(f'[debug_test_view] Error: {tenant_info}')
        import traceback
        logger.warning(f'[debug_test_view] Traceback: {traceback.format_exc()}')
    
    return HttpResponse(f"Debug Test View - {tenant_info} - Path: {request.path}")

# Simple test view that doesn't depend on any imports
def simple_test(request):
    return HttpResponse("SIMPLE TEST WORKS!")

urlpatterns = [
    path('simple-test/', simple_test, name='simple_test'),  # Simplest possible test
    path('admin/', admin.site.urls),
    path('api/', include('tickets.urls')),
    path('api/', include('knowledgebase.urls')),
    path('api/', include('customers.urls')),
    path('debug-test/', debug_test_view, name='debug_test'),  # Test route
    path('', include('frontend.urls')),
]

# Debug: Log that URL patterns are configured
logger.warning(f'URL patterns configured: {len(urlpatterns)} patterns')
