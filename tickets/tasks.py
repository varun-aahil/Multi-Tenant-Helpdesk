"""
Celery tasks for ticket management
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django_tenants.utils import tenant_context

from tenants.models import Client
from .models import Ticket
from .services import TicketService


def _get_active_tenants():
    return Client.objects.filter(is_active=True)


@shared_task
def monitor_sla_deadlines():
    """
    Periodic task to monitor SLA deadlines and trigger escalations
    Runs every minute via Celery Beat
    """
    summary = []
    total_checked = 0
    total_breached = 0

    for tenant in _get_active_tenants():
        with tenant_context(tenant):
            active_tickets = Ticket.objects.filter(
                status__in=['New', 'Open', 'In Progress', 'Reopened']
            ).select_related('assignee', 'customer', 'sla_policy')

            breached_tickets = []
            for ticket in active_tickets:
                if TicketService.check_sla_breach(ticket):
                    breached_tickets.append(ticket)
                    notify_sla_breach.delay(ticket.id, tenant.schema_name)

            summary.append(f"{tenant.schema_name}: {len(breached_tickets)}/{active_tickets.count()}")
            total_checked += active_tickets.count()
            total_breached += len(breached_tickets)

    return f"Checked {total_checked} tickets across tenants. Breaches: {total_breached}. Breakdown: {', '.join(summary)}"


@shared_task
def notify_sla_breach(ticket_id, schema_name):
    """
    Send notification when SLA is breached
    """
    tenant = Client.objects.filter(schema_name=schema_name).first()
    if not tenant:
        return f"Tenant {schema_name} not found"

    with tenant_context(tenant):
        try:
            ticket = Ticket.objects.select_related('assignee', 'customer', 'sla_policy').get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return f"Ticket {ticket_id} not found in tenant {schema_name}"
    
    # Email to assignee if exists
    if ticket.assignee and ticket.assignee.email:
        send_mail(
            subject=f'SLA Breach Alert: {ticket.title}',
            message=f'''
Ticket #{ticket.id} has breached its SLA deadline.

Title: {ticket.title}
Priority: {ticket.priority}
Due At: {ticket.due_at}
Current Status: {ticket.status}

Please take immediate action.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.assignee.email],
            fail_silently=True,
        )
    
    # Email to customer
    if ticket.customer and ticket.customer.email:
        send_mail(
            subject=f'Update on your ticket: {ticket.title}',
            message=f'''
Your ticket #{ticket.id} is being escalated due to SLA deadline.

We apologize for the delay and are working to resolve this issue.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.customer.email],
            fail_silently=True,
        )
    
    return f"Notifications sent for ticket {ticket_id}"


@shared_task
def send_ticket_notification(ticket_id, schema_name, notification_type='created'):
    """
    Send email notification when ticket is created or updated
    """
    tenant = Client.objects.filter(schema_name=schema_name).first()
    if not tenant:
        return f"Tenant {schema_name} not found"

    with tenant_context(tenant):
        try:
            ticket = Ticket.objects.select_related('assignee', 'customer').get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return f"Ticket {ticket_id} not found in tenant {schema_name}"
    
    if notification_type == 'created':
        subject = f'New Ticket Created: {ticket.title}'
        message = f'''
A new ticket has been created:

Title: {ticket.title}
Description: {ticket.description}
Priority: {ticket.priority}
Status: {ticket.status}
        '''
    elif notification_type == 'assigned':
        subject = f'Ticket Assigned: {ticket.title}'
        message = f'''
Ticket #{ticket.id} has been assigned to you:

Title: {ticket.title}
Priority: {ticket.priority}
Due At: {ticket.due_at}
        '''
    else:
        subject = f'Ticket Updated: {ticket.title}'
        message = f'''
Ticket #{ticket.id} has been updated:

Title: {ticket.title}
Status: {ticket.status}
Priority: {ticket.priority}
        '''
    
    # Send to assignee if exists
    if ticket.assignee and ticket.assignee.email:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.assignee.email],
            fail_silently=True,
        )
    
    return f"Notification sent for ticket {ticket_id}"

