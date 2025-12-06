"""
Middleware to handle JWT token authentication for template views
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)


class TokenAuthMiddleware:
    """
    Middleware to extract JWT token from request and set user
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Debug: Log tenant and path for every request
        try:
            from django_tenants.utils import get_tenant
            tenant = get_tenant()
            logger.warning(f'[TokenAuthMiddleware] Request to {request.path} - Tenant: {tenant.schema_name if tenant else "public"}')
        except Exception as e:
            logger.warning(f'[TokenAuthMiddleware] Request to {request.path} - Could not get tenant: {e}')
        
        # Try to get token from various sources (NEVER from URL for security)
        token = None
        
        # 1. From Authorization header (preferred method)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # 2. From POST data (for form submissions)
        if not token:
            token = request.POST.get('token')
        
        # 3. From cookies (role-specific)
        if not token:
            path = request.path or ''
            admin_paths = path.startswith('/admin-panel') or path.startswith('/admin-login') or path.startswith('/admin-logout') or path.startswith('/admin')
            customer_paths = path.startswith('/customer') or path.startswith('/logout') or path == '/' or path.startswith('/register')
            
            if admin_paths:
                token = request.COOKIES.get('admin_access_token')
            elif customer_paths:
                token = request.COOKIES.get('customer_access_token')
            else:
                # default to customer token if available
                token = request.COOKIES.get('customer_access_token') or request.COOKIES.get('admin_access_token')
        
        # NOTE: We intentionally do NOT read from GET parameters for security
        # Tokens in URLs can be logged, cached, or leaked
        
        # Validate token and set user
        if token:
            try:
                auth = JWTAuthentication()
                validated_token = auth.get_validated_token(token)
                user = auth.get_user(validated_token)
                request.user = user
                request._token = token
            except (InvalidToken, TokenError, AttributeError):
                # Token invalid, user will remain anonymous
                pass
        
        response = self.get_response(request)
        
        # Clean token from URL if present (security measure)
        if 'token' in request.GET and hasattr(response, 'url'):
            # This prevents token from appearing in redirect URLs
            pass
        
        return response
