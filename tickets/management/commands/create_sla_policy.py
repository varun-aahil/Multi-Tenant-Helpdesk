"""
Management command to create a custom SLA policy
Usage: python manage.py create_sla_policy --name "Custom Policy" --priority Critical --resolution_time 120
"""
from django.core.management.base import BaseCommand
from tickets.models import SLAPolicy


class Command(BaseCommand):
    help = 'Create a custom SLA policy'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Name of the SLA policy')
        parser.add_argument('--priority', type=str, required=True, 
                          choices=['Low', 'Medium', 'High', 'Critical'],
                          help='Priority level')
        parser.add_argument('--resolution_time', type=int, required=True,
                          help='Resolution time in minutes')
        parser.add_argument('--response_time', type=int, default=None,
                          help='First response time in minutes (optional)')
        parser.add_argument('--business_hours_only', action='store_true',
                          help='Apply only during business hours')
        parser.add_argument('--is_active', action='store_true', default=True,
                          help='Set policy as active')

    def handle(self, *args, **options):
        """Create the SLA policy"""
        # Deactivate existing policy for this priority if creating a new active one
        if options['is_active']:
            SLAPolicy.objects.filter(
                priority=options['priority'],
                is_active=True
            ).update(is_active=False)
        
        policy = SLAPolicy.objects.create(
            name=options['name'],
            priority=options['priority'],
            resolution_time=options['resolution_time'],
            response_time=options.get('response_time'),
            business_hours_only=options.get('business_hours_only', False),
            is_active=options['is_active']
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created SLA policy: {policy.name} ({policy.priority}) - '
                f'{policy.resolution_time} minutes resolution time'
            )
        )

