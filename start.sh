#!/bin/bash

echo "=========================================="
echo "START.SH SCRIPT STARTED"
echo "=========================================="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-not set}"
echo "PORT: ${PORT:-not set}"

echo ""
echo "=========================================="
echo "Ensuring required tables exist..."
echo "=========================================="
python manage.py ensure_tables || echo "ensure_tables command not available, continuing..."

echo ""
echo "=========================================="
echo "Step 1: Running shared schema migrations..."
echo "=========================================="
python manage.py migrate_schemas --shared --verbosity=2

echo ""
echo "=========================================="
echo "Step 2: Running all schema migrations..."
echo "=========================================="
python manage.py migrate_schemas --verbosity=2

echo ""
echo "=========================================="
echo "Checking Django configuration..."
echo "=========================================="
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpdesk_system.settings')
import django
django.setup()
from django.conf import settings
print(f'Database: {settings.DATABASES[\"default\"][\"HOST\"]}')
print(f'DEBUG: {settings.DEBUG}')
print('✅ Django configuration loaded successfully')
" 2>&1 || echo "⚠️  Django configuration check failed, but continuing..."

echo ""
echo "=========================================="
echo "Ensuring default tenant exists..."
echo "=========================================="
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpdesk_system.settings')
import django
django.setup()
from tenants.models import Client, Domain
from django_tenants.utils import tenant_context
from django.core.management import call_command

# Get domain from environment or use default
default_domain = os.environ.get('DEFAULT_TENANT_DOMAIN', '')
default_schema = os.environ.get('DEFAULT_TENANT_SCHEMA', 'default')
default_name = os.environ.get('DEFAULT_TENANT_NAME', 'Default Tenant')

# If no domain specified, try to get from ALLOWED_HOSTS or skip
if not default_domain:
    from django.conf import settings
    if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
        # Try to extract domain from ALLOWED_HOSTS (first non-wildcard)
        for host in settings.ALLOWED_HOSTS:
            if host and host != '*' and '.' in host:
                default_domain = host
                break

if default_domain:
    # Check if tenant already exists
    if not Client.objects.filter(domain_url=default_domain).exists():
        print(f'Creating default tenant: {default_name} ({default_schema}) for domain {default_domain}')
        try:
            tenant = Client(
                schema_name=default_schema,
                name=default_name,
                domain_url=default_domain,
                brand_colors={}
            )
            tenant.save()
            
            # Create domain
            domain = Domain(
                domain=default_domain,
                tenant=tenant,
                is_primary=True
            )
            domain.save()
            
            # Run migrations on tenant schema
            print(f'Running migrations on tenant schema \"{default_schema}\"...')
            with tenant_context(tenant):
                call_command('migrate', verbosity=1, interactive=False)
            
            print(f'✅ Successfully created default tenant \"{default_name}\"')
        except Exception as e:
            print(f'⚠️  Failed to create default tenant: {e}')
    else:
        print(f'✅ Default tenant already exists for domain {default_domain}')
else:
    print('⚠️  No DEFAULT_TENANT_DOMAIN set, skipping tenant creation')
    print('   Set DEFAULT_TENANT_DOMAIN environment variable to auto-create tenant')
" 2>&1 || echo "⚠️  Tenant creation check failed, but continuing..."

echo ""
echo "=========================================="
echo "Starting Gunicorn server..."
echo "=========================================="
if [ -z "$PORT" ]; then
    echo "⚠️  PORT environment variable not set, defaulting to 8000"
    PORT=8000
fi
echo "Binding to 0.0.0.0:$PORT"
echo "Gunicorn command: gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file - --access-logfile - --error-logfile - --timeout 120"
echo "=========================================="
echo "EXECUTING GUNICORN NOW..."
echo "=========================================="
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file - --access-logfile - --error-logfile - --timeout 120

