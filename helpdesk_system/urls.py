"""
URL configuration for helpdesk_system project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tickets.urls')),
    path('api/', include('knowledgebase.urls')),
    path('api/', include('customers.urls')),
    path('', include('frontend.urls')),
]
