from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Public Schema Model - Stores tenant information
    This table is queried first to route traffic to the correct schema
    """
    name = models.CharField(max_length=100)
    schema_name = models.CharField(max_length=63, unique=True, db_index=True)
    domain_url = models.CharField(max_length=255, unique=True, db_index=True)
    brand_colors = models.JSONField(default=dict, help_text="Brand colors for tenant UI customization")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # django-tenants settings
    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        db_table = 'clients'

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain model for django-tenants
    Maps domains to tenants
    """
    pass

