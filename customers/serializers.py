from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    ticket_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'email', 'name', 'phone', 'company',
            'ticket_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
    
    def get_ticket_count(self, obj):
        """Get number of tickets for this customer"""
        return obj.tickets.count()


class CustomerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'company', 'created_at']

