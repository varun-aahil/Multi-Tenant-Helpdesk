"""
Management command to ensure required tables exist.
This handles the case where migrations are marked as applied but tables don't exist.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Ensure required tables exist, creating them if needed'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Check if clients table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'clients'
            );
        """)
        clients_exists = cursor.fetchone()[0]
        
        # Check if tenants_domain table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'tenants_domain'
            );
        """)
        domain_exists = cursor.fetchone()[0]
        
        if not clients_exists or not domain_exists:
            self.stdout.write(self.style.WARNING(
                f'Missing tables: clients={not clients_exists}, tenants_domain={not domain_exists}'
            ))
            self.stdout.write('Running migrations to create missing tables...')
            
            # Force run migrations - delete migration records and reapply
            try:
                # Delete migration records for tenants app to force reapplication
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'tenants';
                """)
                self.stdout.write('Cleared migration records for tenants app')
                
                # Now run migrations
                call_command('migrate_schemas', '--shared', verbosity=2)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Migration error: {e}'))
                # If migration fails, we'll continue anyway
        else:
            self.stdout.write(self.style.SUCCESS('All required tables exist!'))

