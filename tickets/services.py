"""
Business Logic Layer for Tickets
Complex logic abstracted from Views
"""
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime, time as dt_time
from .models import Ticket, SLAPolicy


class TicketService:
    """
    Service class for ticket business logic
    """
    
    @staticmethod
    def _get_default_resolution_minutes(priority: str) -> int:
        defaults = {
            'Critical': 4 * 60,   # 4 hours
            'High': 12 * 60,      # 12 hours
            'Medium': 24 * 60,    # 1 day
            'Low': 72 * 60,       # 3 days
        }
        return defaults.get(priority, 24 * 60)
    
    @staticmethod
    def calculate_due_at(ticket: Ticket, sla_policy: SLAPolicy = None) -> datetime:
        """
        Calculate due_at timestamp based on SLA policy and business hours
        """
        base_time = timezone.now()
        
        if not sla_policy:
            sla_policy = SLAPolicy.objects.filter(
                priority=ticket.priority,
                is_active=True
            ).first()
        
        if sla_policy:
            resolution_minutes = sla_policy.resolution_time or 0
            if resolution_minutes <= 0:
                resolution_minutes = TicketService._get_default_resolution_minutes(ticket.priority)
            if sla_policy.business_hours_only:
                return TicketService._calculate_business_hours_due(
                    base_time,
                    resolution_minutes
                )
            return base_time + relativedelta(minutes=resolution_minutes)
        
        # No SLA policy found, use sensible defaults per priority
        fallback_minutes = TicketService._get_default_resolution_minutes(ticket.priority)
        return base_time + relativedelta(minutes=fallback_minutes)
            
    @staticmethod
    def _calculate_business_hours_due(start_time: datetime, minutes: int) -> datetime:
        """
        Calculate due time considering only business hours (9 AM - 5 PM, Mon-Fri)
        """
        current = start_time
        remaining_minutes = minutes
        
        # Business hours: 9:00 AM to 5:00 PM
        business_start = dt_time(9, 0)
        business_end = dt_time(17, 0)
        
        while remaining_minutes > 0:
            # Skip weekends
            if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
                # Move to next Monday 9 AM
                days_ahead = 7 - current.weekday()
                current = current.replace(hour=9, minute=0, second=0, microsecond=0)
                current = current + relativedelta(days=days_ahead)
                continue
            
            # Get current day's business hours
            day_start = current.replace(hour=business_start.hour, minute=business_start.minute, second=0, microsecond=0)
            day_end = current.replace(hour=business_end.hour, minute=business_end.minute, second=0, microsecond=0)
            
            # If before business hours, move to start of day
            if current < day_start:
                current = day_start
            
            # If after business hours, move to next day
            if current >= day_end:
                current = current + relativedelta(days=1)
                current = current.replace(hour=business_start.hour, minute=business_start.minute, second=0, microsecond=0)
                continue
            
            # Calculate how many minutes left in current business day
            minutes_left_today = (day_end - current).total_seconds() / 60
            
            if remaining_minutes <= minutes_left_today:
                # Can finish within today
                current = current + relativedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                # Need to continue to next day
                remaining_minutes -= minutes_left_today
                current = current + relativedelta(days=1)
                current = current.replace(hour=business_start.hour, minute=business_start.minute, second=0, microsecond=0)
        
        return current
    
    @staticmethod
    def update_ticket_status(ticket: Ticket, new_status: str, user=None):
        """
        Update ticket status with proper state machine logic
        """
        old_status = ticket.status
        ticket.status = new_status
        
        # Track first response
        if old_status == 'New' and new_status in ['Open', 'In Progress']:
            if not ticket.first_response_at:
                ticket.first_response_at = timezone.now()
        
        # Track resolution
        if new_status == 'Resolved' and old_status != 'Resolved':
            ticket.resolved_at = timezone.now()
        elif new_status != 'Resolved' and old_status == 'Resolved':
            ticket.resolved_at = None
        
        ticket.save()
        return ticket
    
    @staticmethod
    def assign_ticket(ticket: Ticket, assignee, sla_policy: SLAPolicy = None):
        """
        Assign ticket and recalculate due_at
        """
        ticket.assignee = assignee
        if sla_policy or not ticket.due_at:
            ticket.due_at = TicketService.calculate_due_at(ticket, sla_policy)
        ticket.save()
        return ticket
    
    @staticmethod
    def check_sla_breach(ticket: Ticket) -> bool:
        """
        Check if ticket has breached SLA
        """
        if not ticket.due_at:
            return False
        
        return timezone.now() > ticket.due_at and ticket.status not in ['Resolved', 'Closed']

    @staticmethod
    def get_time_to_escalation(ticket: Ticket):
        if not ticket.due_at:
            return None
        return ticket.due_at - timezone.now()

    @staticmethod
    def format_time_to_escalation(ticket: Ticket):
        delta = TicketService.get_time_to_escalation(ticket)
        if delta is None:
            return {
                'label': 'No SLA deadline',
                'is_overdue': False,
                'seconds': None,
            }
        
        total_seconds = int(delta.total_seconds())
        # Don't mark as overdue if ticket is resolved or closed
        is_overdue = total_seconds <= 0 and ticket.status not in ['Resolved', 'Closed']
        remaining = abs(total_seconds)
        
        days, remainder = divmod(remaining, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = remainder // 60
        
        if days > 0:
            time_str = f"{days}d {hours}h"
        elif hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            if minutes == 0:
                minutes = 1
            time_str = f"{minutes}m"
        
        # If ticket is resolved or closed, show resolved status instead of overdue
        if ticket.status in ['Resolved', 'Closed']:
            label = f"Resolved"
        elif is_overdue:
            label = f"Overdue by {time_str}"
        else:
            label = f"Escalates in {time_str}"
        
        return {
            'label': label,
            'is_overdue': is_overdue,
            'seconds': total_seconds,
        }

