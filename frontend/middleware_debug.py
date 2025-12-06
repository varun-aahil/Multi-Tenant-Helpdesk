"""
Debug middleware to trace request processing and tenant routing
"""
import logging
import sys

# Force logging to stderr to ensure it appears
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.warning('[middleware_debug] MODULE LOADED!')


class DebugTenantMiddleware:
    """
    Debug middleware to log tenant routing and URL resolution
    """
    def __init__(self, get_response):
        logger.warning('[DebugTenantMiddleware] __init__ called!')
        self.get_response = get_response

    def __call__(self, request):
        # Force immediate logging to stderr
        import sys
        print(f'[DebugTenantMiddleware] __call__ EXECUTED! Request: {request.method} {request.path}', file=sys.stderr, flush=True)
        logger.warning(f'[DebugTenantMiddleware] Request: {request.method} {request.path}')
        logger.warning(f'[DebugTenantMiddleware] Host: {request.get_host()}')
        logger.warning(f'[DebugTenantMiddleware] META HTTP_HOST: {request.META.get("HTTP_HOST", "N/A")}')
        
        # Try to get tenant
        try:
            from django_tenants.utils import get_tenant
            tenant = get_tenant()
            if tenant:
                logger.warning(f'[DebugTenantMiddleware] Tenant found: {tenant.schema_name}')
            else:
                logger.warning(f'[DebugTenantMiddleware] No tenant found (public schema)')
        except Exception as e:
            logger.warning(f'[DebugTenantMiddleware] Error getting tenant: {e}')
            import traceback
            logger.warning(f'[DebugTenantMiddleware] Traceback: {traceback.format_exc()}')
        
        print(f'[DebugTenantMiddleware] About to call get_response', file=sys.stderr, flush=True)
        response = self.get_response(request)
        print(f'[DebugTenantMiddleware] Got response: {response.status_code}', file=sys.stderr, flush=True)
        
        logger.warning(f'[DebugTenantMiddleware] Response status: {response.status_code}')
        
        return response

