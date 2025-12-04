from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, SLAPolicyViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'sla-policies', SLAPolicyViewSet, basename='sla-policy')

urlpatterns = [
    path('', include(router.urls)),
]

