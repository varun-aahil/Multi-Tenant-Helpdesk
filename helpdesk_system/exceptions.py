"""
Custom exception handler for DRF
Returns unified error responses
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in format:
    {"code": "ERROR_CODE", "message": "Error message"}
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception
    if response is None:
        if isinstance(exc, ValidationError):
            return Response(
                {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Customize the response data structure
    custom_response_data = {
        "code": _get_error_code(exc),
        "message": _get_error_message(exc, response)
    }

    # Add details if available
    if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
        custom_response_data["details"] = exc.detail

    response.data = custom_response_data
    return response


def _get_error_code(exc):
    """Extract error code from exception"""
    error_code_map = {
        'ValidationError': 'VALIDATION_ERROR',
        'PermissionDenied': 'PERMISSION_DENIED',
        'AuthenticationFailed': 'AUTHENTICATION_ERROR',
        'NotFound': 'NOT_FOUND',
        'SLAError': 'SLA_ERROR',
    }
    
    exc_name = exc.__class__.__name__
    return error_code_map.get(exc_name, 'ERROR')


def _get_error_message(exc, response):
    """Extract error message from exception"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        elif isinstance(exc.detail, list):
            return '; '.join([str(item) for item in exc.detail])
        elif isinstance(exc.detail, dict):
            # Return first error message
            for key, value in exc.detail.items():
                if isinstance(value, list):
                    return f"{key}: {value[0]}"
                return f"{key}: {value}"
    
    return str(exc) if str(exc) else "An error occurred"

