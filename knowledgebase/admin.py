from django.contrib import admin
from .models import KnowledgeBase


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'view_count', 'created_by', 'created_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'tags')
    readonly_fields = ('view_count', 'created_at', 'updated_at', 'created_by')
    fields = ('title', 'content', 'category', 'tags', 'is_published', 'created_by', 'view_count', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set"""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to make created_by read-only"""
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # Creating new object
            # Don't show created_by field when creating (will be set automatically)
            if 'created_by' in form.base_fields:
                form.base_fields['created_by'].widget = admin.widgets.AdminTextInputWidget()
                form.base_fields['created_by'].required = False
        return form

