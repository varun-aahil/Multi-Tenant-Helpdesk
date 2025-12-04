from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Client, Domain


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin for tenants (clients).

    Only the global superuser should be able to view or manage tenants.
    Tenant-specific staff/admins must not see or edit these objects, which
    prevents them from seeing cross-tenant history.
    """

    list_display = ("name", "schema_name", "domain_url", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "schema_name", "domain_url")

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """
    Admin for tenant domains.

    Also restricted to the global superuser only.
    """

    list_display = ("domain", "tenant", "is_primary")

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user and request.user.is_superuser)


