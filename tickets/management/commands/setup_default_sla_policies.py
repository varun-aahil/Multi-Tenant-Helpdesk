"""
Management command to create default SLA policies for a tenant
"""
from django.core.management.base import BaseCommand
from tickets.models import SLAPolicy


class Command(BaseCommand):
    help = 'Create default SLA policies for the current tenant schema'

    def handle(self, *args, **options):
        """Create default SLA policies if they don't exist"""
        
        default_policies = [
            {
                'name': 'Critical Priority SLA',
                'priority': 'Critical',
                'resolution_time': 240,  # 4 hours in minutes
                'response_time': 60,     # 1 hour
                'business_hours_only': False,
                'is_active': True,
            },
            {
                'name': 'High Priority SLA',
                'priority': 'High',
                'resolution_time': 720,  # 12 hours in minutes
                'response_time': 120,     # 2 hours
                'business_hours_only': False,
                'is_active': True,
            },
            {
                'name': 'Medium Priority SLA',
                'priority': 'Medium',
                'resolution_time': 1440,  # 24 hours (1 day) in minutes
                'response_time': 240,     # 4 hours
                'business_hours_only': False,
                'is_active': True,
            },
            {
                'name': 'Low Priority SLA',
                'priority': 'Low',
                'resolution_time': 4320,  # 72 hours (3 days) in minutes
                'response_time': 480,      # 8 hours
                'business_hours_only': False,
                'is_active': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for policy_data in default_policies:
            policy, created = SLAPolicy.objects.get_or_create(
                priority=policy_data['priority'],
                is_active=True,
                defaults=policy_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created SLA policy: {policy.name} ({policy.priority}) - {policy.resolution_time} minutes'
                    )
                )
            else:
                # Update existing policy if values differ
                updated = False
                for key, value in policy_data.items():
                    if key not in ['priority', 'is_active'] and getattr(policy, key) != value:
                        setattr(policy, key, value)
                        updated = True
                
                if updated:
                    policy.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated SLA policy: {policy.name} ({policy.priority})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'SLA policy already exists: {policy.name} ({policy.priority})'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSLA Policies Setup Complete: {created_count} created, {updated_count} updated'
            )
        )

