from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import json

User = get_user_model()


class SLAPolicy(models.Model):
    """
    Tenant Schema Model - SLA Policy definitions
    Defines rules like {"priority": "High", "resolution_time": 60}
    """
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    name = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    resolution_time = models.IntegerField(help_text="Resolution time in minutes")
    response_time = models.IntegerField(help_text="First response time in minutes", null=True, blank=True)
    business_hours_only = models.BooleanField(default=False, help_text="Apply only during business hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sla_policies'
        verbose_name_plural = 'SLA Policies'
        unique_together = ['priority', 'is_active']

    def __str__(self):
        return f"{self.name} - {self.priority} ({self.resolution_time} min)"


class Ticket(models.Model):
    """
    Tenant Schema Model - Support tickets
    """
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
        ('Reopened', 'Reopened'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    
    # Relationships
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    sla_policy = models.ForeignKey(SLAPolicy, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    # SLA tracking
    due_at = models.DateTimeField(null=True, blank=True, help_text="Calculated based on SLA policy")
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    tags = models.JSONField(default=list, blank=True)
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment URLs/paths")

    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    def clean(self):
        """Business constraint validation"""
        # Cannot move from Resolved to New without reason
        if self.pk:
            old_instance = Ticket.objects.get(pk=self.pk)
            if old_instance.status == 'Resolved' and self.status == 'New':
                raise ValidationError("A ticket cannot move from Resolved to New without a reason")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
