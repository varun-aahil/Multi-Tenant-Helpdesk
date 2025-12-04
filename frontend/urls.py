"""
URLs for frontend views
"""
from django.urls import path
from . import views

urlpatterns = [
    # Customer panel
    path('', views.customer_login, name='customer_login'),
    path('register/', views.customer_register, name='customer_register'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/tickets/', views.customer_tickets, name='customer_tickets'),
    path('customer/tickets/create/', views.customer_create_ticket, name='customer_create_ticket'),
    path('customer/tickets/<int:ticket_id>/', views.customer_ticket_detail, name='customer_ticket_detail'),
    path('customer/knowledge-base/', views.customer_knowledge_base, name='customer_knowledge_base'),
    path('customer/knowledge-base/<int:article_id>/', views.customer_kb_article, name='customer_kb_article'),
    
    # Admin panel
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin-panel/tickets/<int:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),
    path('admin-panel/customers/', views.admin_customers, name='admin_customers'),
    path('admin-panel/knowledge-base/', views.admin_knowledge_base, name='admin_knowledge_base'),
    path('admin-panel/knowledge-base/<int:article_id>/', views.admin_kb_article_detail, name='admin_kb_article_detail'),
]

