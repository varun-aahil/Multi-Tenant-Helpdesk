from django.contrib import admin

from .models import Ticket, SLAPolicy
from .services import TicketService


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'resolution_time', 'response_time', 'business_hours_only', 'is_active')
    list_filter = ('is_active', 'priority', 'business_hours_only')
    search_fields = ('name', 'priority')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'customer', 'assignee', 'due_at', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'assignee')
    search_fields = ('title', 'description', 'customer__name', 'customer__email')
    readonly_fields = ('created_at', 'updated_at', 'first_response_at', 'resolved_at')
    date_hierarchy = 'created_at'

    def save_model(self, request, obj, form, change):
        """
        Ensure SLA due_at is calculated for tickets created/edited via admin.

        - If due_at is empty but we have an SLA policy (or at least a priority),
          compute it using TicketService.
        - If due_at is already set (e.g. manually overridden), respect that.
        """
        if not obj.due_at:
            obj.due_at = TicketService.calculate_due_at(obj, obj.sla_policy if hasattr(obj, "sla_policy") else None)
        super().save_model(request, obj, form, change)
