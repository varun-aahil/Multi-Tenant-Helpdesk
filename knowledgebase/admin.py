from django.contrib import admin
from .models import KnowledgeBase


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'view_count', 'created_by', 'created_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'tags')
    readonly_fields = ('view_count', 'created_at', 'updated_at')

