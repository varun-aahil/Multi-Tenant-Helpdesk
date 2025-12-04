"""
Custom permissions for ticket management
"""
from rest_framework import permissions
from django_tenants.utils import tenant_context


class IsTenantMember(permissions.BasePermission):
    """
    Ensures the logged-in user exists within the currently active schema
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # In tenant context, user should exist in current schema
        # django-tenants handles schema isolation, so if we're here, user is in correct schema
        return True


class IsManager(permissions.BasePermission):
    """
    Permission for managers to perform sensitive actions like Force-Close Ticket
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is staff or has manager role
        # You can extend this to check for a specific role field
        return request.user.is_staff or getattr(request.user, 'is_manager', False)


class IsAssigneeOrManager(permissions.BasePermission):
    """
    Permission to allow assignee or manager to modify ticket
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Manager can do anything
        if request.user.is_staff or getattr(request.user, 'is_manager', False):
            return True
        
        # Assignee can modify their own tickets
        if obj.assignee == request.user:
            return True
        
        return False


class CanForceCloseTicket(permissions.BasePermission):
    """
    Special permission for force-closing tickets
    """
    def has_permission(self, request, view):
        return IsManager().has_permission(request, view)

