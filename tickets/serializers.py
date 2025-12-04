from rest_framework import serializers
from .models import Ticket, SLAPolicy
from customers.models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()


class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class TicketSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(write_only=True, required=False)
    customer_name = serializers.CharField(write_only=True, required=False)
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    customer_name_display = serializers.CharField(source='customer.name', read_only=True)
    customer_email_display = serializers.EmailField(source='customer.email', read_only=True)
    sla_policy_name = serializers.CharField(source='sla_policy.name', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'customer', 'customer_email', 'customer_name',
            'customer_name_display', 'customer_email_display',
            'assignee', 'assignee_username', 'sla_policy', 'sla_policy_name',
            'due_at', 'first_response_at', 'resolved_at',
            'tags', 'attachments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at', 'first_response_at', 'resolved_at', 'due_at')
    
    def validate_due_at(self, value):
        """Ensure due_at is a future timestamp"""
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError("due_at must be a future timestamp")
        return value
    
    def create(self, validated_data):
        """Create ticket with customer lookup or creation"""
        customer_email = validated_data.pop('customer_email', None)
        customer_name = validated_data.pop('customer_name', None)
        
        # Get or create customer
        if customer_email:
            customer, _ = Customer.objects.get_or_create(
                email=customer_email,
                defaults={'name': customer_name or customer_email.split('@')[0]}
            )
            validated_data['customer'] = customer
        
        # Calculate due_at if not provided
        ticket = Ticket(**validated_data)
        if not ticket.due_at:
            from .services import TicketService
            ticket.due_at = TicketService.calculate_due_at(ticket)
        
        ticket.save()
        return ticket
    
    def update(self, instance, validated_data):
        """Update ticket with status change tracking"""
        customer_email = validated_data.pop('customer_email', None)
        customer_name = validated_data.pop('customer_name', None)
        
        if customer_email:
            customer, _ = Customer.objects.get_or_create(
                email=customer_email,
                defaults={'name': customer_name or customer_email.split('@')[0]}
            )
            validated_data['customer'] = customer
        
        # Track status changes
        if 'status' in validated_data:
            from .services import TicketService
            TicketService.update_ticket_status(instance, validated_data['status'])
            validated_data.pop('status')  # Already handled by service
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'status', 'priority',
            'customer_name', 'assignee_username',
            'due_at', 'is_overdue', 'created_at'
        ]
    
    def get_is_overdue(self, obj):
        from .services import TicketService
        return TicketService.check_sla_breach(obj)

