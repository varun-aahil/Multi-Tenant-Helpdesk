from django.contrib import admin
from django import forms
from .models import KnowledgeBase
import json


class TagsJSONWidget(forms.Textarea):
    """Custom widget for tags JSONField that accepts comma-separated values"""
    def format_value(self, value):
        """Convert JSON list to comma-separated string for display"""
        if value is None:
            return ''
        if isinstance(value, list):
            return ', '.join(str(tag) for tag in value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return ', '.join(str(tag) for tag in parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        return str(value)
    
    def value_from_datadict(self, data, files, name):
        """Convert comma-separated string to JSON list"""
        value = data.get(name, '')
        if not value:
            return '[]'
        
        # Try to parse as JSON first
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # If not valid JSON, treat as comma-separated values
        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        return json.dumps(tags)


class KnowledgeBaseAdminForm(forms.ModelForm):
    """Custom form for KnowledgeBase with better tags handling"""
    tags = forms.CharField(
        widget=TagsJSONWidget(attrs={'rows': 3, 'cols': 40}),
        help_text='Enter tags separated by commas (e.g., "tag1, tag2, tag3") or as JSON array (e.g., ["tag1", "tag2"])',
        required=False
    )
    
    class Meta:
        model = KnowledgeBase
        fields = '__all__'
    
    def clean_tags(self):
        """Ensure tags is always a valid JSON list"""
        tags = self.cleaned_data.get('tags', '[]')
        if not tags:
            return []
        
        # Try to parse as JSON
        try:
            parsed = json.loads(tags)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        
        # If not JSON, treat as comma-separated
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        return tag_list


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    form = KnowledgeBaseAdminForm
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
