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

# Get domain from environment, Render service URL, or ALLOWED_HOSTS
default_domain = os.environ.get('DEFAULT_TENANT_DOMAIN', '')
default_schema = os.environ.get('DEFAULT_TENANT_SCHEMA', 'default')
default_name = os.environ.get('DEFAULT_TENANT_NAME', 'Default Tenant')

# Try to get from Render's service URL (if available)
if not default_domain:
    render_url = os.environ.get('RENDER_SERVICE_URL') or os.environ.get('RENDER_EXTERNAL_URL')
    if render_url:
        # Extract domain from URL (remove https:// and path)
        from urllib.parse import urlparse
        parsed = urlparse(render_url)
        if parsed.netloc:
            default_domain = parsed.netloc
            print(f'📋 Detected domain from Render service URL: {default_domain}')

# If still no domain, try to get from ALLOWED_HOSTS
if not default_domain:
    from django.conf import settings
    if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
        # Try to extract domain from ALLOWED_HOSTS (first non-wildcard, non-localhost)
        for host in settings.ALLOWED_HOSTS:
            if host and host != '*' and '.' in host and 'localhost' not in host.lower():
                default_domain = host
                print(f'📋 Detected domain from ALLOWED_HOSTS: {default_domain}')
                break

# Also check Domain model (django-tenants uses this for routing)
domains_to_check = [default_domain] if default_domain else []
if default_domain and default_domain != os.environ.get('DEFAULT_TENANT_DOMAIN', ''):
    # Also check if we need to create tenant for all ALLOWED_HOSTS
    from django.conf import settings
    if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
        for host in settings.ALLOWED_HOSTS:
            if host and host != '*' and '.' in host and 'localhost' not in host.lower() and host not in domains_to_check:
                domains_to_check.append(host)

if default_domain:
    # Check if tenant already exists (by domain_url or Domain model)
    tenant_exists = False
    existing_tenant = None
    
    # Check by domain_url
    if Client.objects.filter(domain_url=default_domain).exists():
        tenant_exists = True
        existing_tenant = Client.objects.filter(domain_url=default_domain).first()
        print(f'✅ Tenant found by domain_url: {default_domain}')
    
    # Also check Domain model (this is what django-tenants actually uses)
    if Domain.objects.filter(domain=default_domain).exists():
        tenant_exists = True
        domain_obj = Domain.objects.filter(domain=default_domain).first()
        existing_tenant = domain_obj.tenant
        print(f'✅ Tenant found by Domain model: {default_domain}')
    
    if not tenant_exists:
        print(f'🔧 Creating default tenant: {default_name} ({default_schema}) for domain {default_domain}')
        try:
            # Check if schema already exists (from a previous tenant creation)
            schema_exists = False
            try:
                with tenant_context(Client.objects.filter(schema_name=default_schema).first()):
                    schema_exists = True
            except:
                pass
            
            # Create tenant only if schema doesn't exist
            if not Client.objects.filter(schema_name=default_schema).exists():
                tenant = Client(
                    schema_name=default_schema,
                    name=default_name,
                    domain_url=default_domain,
                    brand_colors={}
                )
                tenant.save()
            else:
                # Use existing tenant with this schema
                tenant = Client.objects.filter(schema_name=default_schema).first()
                # Update domain_url if different
                if tenant.domain_url != default_domain:
                    print(f'📝 Updating tenant domain_url from {tenant.domain_url} to {default_domain}')
                    tenant.domain_url = default_domain
                    tenant.save()
            
            # Create or update Domain record (this is what django-tenants uses for routing)
            print(f'🔗 Creating/updating Domain record for {default_domain}...')
            domain, created = Domain.objects.get_or_create(
                domain=default_domain,
                defaults={
                    'tenant': tenant,
                    'is_primary': True
                }
            )
            if created:
                print(f'✅ Created new Domain record for {default_domain}')
            else:
                # Domain exists but might point to wrong tenant - update it
                print(f'📝 Domain record already exists, checking if update needed...')
                if domain.tenant != tenant:
                    print(f'📝 Updating Domain record to point to correct tenant')
                    domain.tenant = tenant
                    domain.is_primary = True
                    domain.save()
                    print(f'✅ Updated Domain record')
                else:
                    print(f'✅ Domain record already correctly configured')
            
            # Run migrations on tenant schema (always run to ensure tables exist)
            print(f'📦 Running migrations on tenant schema \"{default_schema}\"...')
            with tenant_context(tenant):
                call_command('migrate', verbosity=2, interactive=False)
                print(f'✅ Migrations completed for tenant schema \"{default_schema}\"')
                
                # Setup default SLA policies
                print(f'📋 Setting up default SLA policies for tenant schema \"{default_schema}\"...')
                try:
                    call_command('setup_default_sla_policies', verbosity=1)
                    print(f'✅ SLA policies created for tenant schema \"{default_schema}\"')
                except Exception as e:
                    print(f'⚠️  SLA policy setup failed (non-critical): {e}')
                
                # Create admin user
                print(f'👤 Creating admin user for tenant schema \"{default_schema}\"...')
                try:
                    call_command('create_admin_user', 
                                username='root', 
                                password='varun16728...',
                                email='admin@example.com',
                                verbosity=1)
                    print(f'✅ Admin user created for tenant schema \"{default_schema}\"')
                except Exception as e:
                    print(f'⚠️  Admin user creation failed (non-critical): {e}')
            
            print(f'✅ Successfully created/updated tenant \"{default_name}\" for domain {default_domain}')
            
            # Verify Domain record exists and is queryable
            try:
                verify_domain = Domain.objects.filter(domain=default_domain).first()
                if verify_domain:
                    print(f'✅ Verification: Domain record exists for {default_domain}, points to tenant: {verify_domain.tenant.name}')
                else:
                    print(f'⚠️  WARNING: Domain record not found after creation!')
            except Exception as e:
                print(f'⚠️  WARNING: Could not verify Domain record: {e}')
        except Exception as e:
            print(f'⚠️  Failed to create default tenant: {e}')
            import traceback
            traceback.print_exc()
    else:
        # Tenant exists, but ensure Domain record exists too
        print(f'🔍 Checking if Domain record exists for {default_domain}...')
        domain_obj = Domain.objects.filter(domain=default_domain).first()
        if not domain_obj:
            print(f'🔧 Adding Domain record for existing tenant: {default_domain}')
            try:
                domain_obj = Domain(
                    domain=default_domain,
                    tenant=existing_tenant,
                    is_primary=True
                )
                domain_obj.save()
                print(f'✅ Added Domain record for {default_domain}')
            except Exception as e:
                print(f'⚠️  Failed to add Domain record: {e}')
                import traceback
                traceback.print_exc()
        else:
            # Verify it points to the correct tenant
            if domain_obj.tenant != existing_tenant:
                print(f'📝 Updating Domain record to point to correct tenant')
                domain_obj.tenant = existing_tenant
                domain_obj.is_primary = True
                domain_obj.save()
                print(f'✅ Updated Domain record')
            else:
                print(f'✅ Domain record exists and is correctly configured for {default_domain}')
        
               # Always ensure migrations are run on existing tenant schema
               print(f'📦 Ensuring migrations are up to date for tenant schema \"{existing_tenant.schema_name}\"...')
               try:
                   with tenant_context(existing_tenant):
                       call_command('migrate', verbosity=2, interactive=False)
                       print(f'✅ Migrations verified for tenant schema \"{existing_tenant.schema_name}\"')
                       
                       # Setup default SLA policies if they don't exist
                       print(f'📋 Setting up default SLA policies for tenant schema \"{existing_tenant.schema_name}\"...')
                       try:
                           call_command('setup_default_sla_policies', verbosity=1)
                           print(f'✅ SLA policies verified for tenant schema \"{existing_tenant.schema_name}\"')
                       except Exception as e:
                           print(f'⚠️  SLA policy setup failed (non-critical): {e}')
                       
                       # Create admin user if it doesn't exist
                       print(f'👤 Ensuring admin user exists for tenant schema \"{existing_tenant.schema_name}\"...')
                       try:
                           call_command('create_admin_user', 
                                       username='root', 
                                       password='varun16728...',
                                       email='admin@example.com',
                                       verbosity=1)
                           print(f'✅ Admin user verified for tenant schema \"{existing_tenant.schema_name}\"')
                       except Exception as e:
                           print(f'⚠️  Admin user setup failed (non-critical): {e}')
               except Exception as e:
                   print(f'⚠️  Migration check failed for tenant schema: {e}')
                   import traceback
                   traceback.print_exc()
else:
    print('⚠️  Could not determine domain for tenant creation')
    print('   Options:')
    print('   1. Set DEFAULT_TENANT_DOMAIN environment variable')
    print('   2. Ensure ALLOWED_HOSTS contains your domain')
    print('   3. Create tenant manually when you have shell access')
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

