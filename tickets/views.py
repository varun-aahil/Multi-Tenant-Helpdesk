from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Ticket, SLAPolicy
from .serializers import TicketSerializer, TicketListSerializer, SLAPolicySerializer
from .permissions import IsTenantMember, IsAssigneeOrManager, CanForceCloseTicket
from .services import TicketService


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Ticket CRUD operations
    Automatically filters by tenant schema
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        """
        Override to filter by tenant schema automatically
        django-tenants ensures we're in the correct schema context
        """
        queryset = Ticket.objects.all()
        
        # Additional filtering based on user role
        if not (self.request.user.is_staff or getattr(self.request.user, 'is_manager', False)):
            # Regular users only see their assigned tickets or tickets they created
            queryset = queryset.filter(
                Q(assignee=self.request.user) | Q(customer__email=self.request.user.email)
            )
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = self.request.query_params.get('priority', None)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Filter by assignee if provided
        assignee_filter = self.request.query_params.get('assignee', None)
        if assignee_filter:
            queryset = queryset.filter(assignee_id=assignee_filter)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.select_related('customer', 'assignee', 'sla_policy')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        return TicketSerializer
    
    def perform_create(self, serializer):
        """Create ticket with automatic SLA calculation"""
        ticket = serializer.save()
        # Ensure due_at is calculated
        if not ticket.due_at:
            ticket.due_at = TicketService.calculate_due_at(ticket)
            ticket.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAssigneeOrManager])
    def assign(self, request, pk=None):
        """Assign ticket to an agent"""
        ticket = self.get_object()
        assignee_id = request.data.get('assignee_id')
        
        if not assignee_id:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'assignee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assignee = User.objects.get(pk=assignee_id)
        except User.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': 'Assignee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        TicketService.assign_ticket(ticket, assignee)
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAssigneeOrManager])
    def change_status(self, request, pk=None):
        """Change ticket status"""
        ticket = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Ticket.STATUS_CHOICES):
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        TicketService.update_ticket_status(ticket, new_status, request.user)
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanForceCloseTicket])
    def force_close(self, request, pk=None):
        """Force close ticket (Manager only)"""
        ticket = self.get_object()
        TicketService.update_ticket_status(ticket, 'Closed', request.user)
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue tickets"""
        queryset = self.get_queryset()
        overdue_tickets = [ticket for ticket in queryset if TicketService.check_sla_breach(ticket)]
        serializer = self.get_serializer(overdue_tickets, many=True)
        return Response(serializer.data)


class SLAPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SLA Policy CRUD operations
    """
    queryset = SLAPolicy.objects.all()
    serializer_class = SLAPolicySerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        """Filter by active status if requested"""
        queryset = SLAPolicy.objects.all()
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset
