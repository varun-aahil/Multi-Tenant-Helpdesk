"""
Management command to create a new tenant
Usage: python manage.py create_tenant_custom --schema_name acme --name "Acme Corp" --domain_url acme.localhost
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django_tenants.utils import tenant_context
from tenants.models import Client, Domain
import json


class Command(BaseCommand):
    help = 'Create a new tenant with schema and domain'

    def add_arguments(self, parser):
        parser.add_argument('--schema_name', type=str, required=True, help='Schema name (e.g., acme)')
        parser.add_argument('--name', type=str, required=True, help='Tenant name (e.g., Acme Corp)')
        parser.add_argument('--domain_url', type=str, required=True, help='Domain URL (e.g., acme.localhost)')
        parser.add_argument('--brand_colors', type=str, default='{}', help='Brand colors JSON (default: {})')

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        name = options['name']
        domain_url = options['domain_url']
        brand_colors_str = options['brand_colors']

        # Check if tenant already exists
        if Client.objects.filter(schema_name=schema_name).exists():
            self.stdout.write(self.style.ERROR(f'Tenant with schema_name "{schema_name}" already exists'))
            return

        if Client.objects.filter(domain_url=domain_url).exists():
            self.stdout.write(self.style.ERROR(f'Tenant with domain_url "{domain_url}" already exists'))
            return

        # Parse brand colors
        try:
            brand_colors = json.loads(brand_colors_str) if brand_colors_str != '{}' else {}
        except json.JSONDecodeError:
            self.stdout.write(self.style.WARNING(f'Invalid JSON for brand_colors, using empty dict'))
            brand_colors = {}

        # Create tenant (this will auto-create the schema if auto_create_schema=True)
        tenant = Client(
            schema_name=schema_name,
            name=name,
            domain_url=domain_url,
            brand_colors=brand_colors
        )
        tenant.save()

        # Create domain
        domain = Domain(
            domain=domain_url,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        # Run migrations on the tenant schema
        self.stdout.write(self.style.WARNING(f'Running migrations on tenant schema "{schema_name}"...'))
        with tenant_context(tenant):
            call_command('migrate', verbosity=1, interactive=False)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created tenant "{name}" with schema "{schema_name}" and domain "{domain_url}"'
        ))

