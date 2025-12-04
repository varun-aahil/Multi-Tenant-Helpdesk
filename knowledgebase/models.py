from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KnowledgeBase(models.Model):
    """
    Tenant Schema Model - Knowledge Base articles specific to each tenant
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, help_text="List of tags for categorization")
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='knowledge_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_base'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

