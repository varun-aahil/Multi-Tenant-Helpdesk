from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Customer
from .serializers import CustomerSerializer, CustomerListSerializer
from tickets.permissions import IsTenantMember


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Customer CRUD operations
    """
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    serializer_class = CustomerSerializer
    
    def get_queryset(self):
        """Filter customers with search"""
        queryset = Customer.objects.all()
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(company__icontains=search)
            )
        
        return queryset.prefetch_related('tickets')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer
