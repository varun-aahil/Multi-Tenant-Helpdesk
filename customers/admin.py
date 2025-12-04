from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'company')

