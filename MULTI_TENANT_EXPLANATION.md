# Multi-Tenant Architecture Explanation

## How Django-Tenants Works

Your helpdesk system uses **django-tenants**, which implements multi-tenancy using **PostgreSQL schemas**. Here's how it works:

### 1. **Schema Isolation**

Each tenant has its own PostgreSQL schema (like a separate database within the same database):
- **Public Schema**: Contains shared data (tenant definitions, domains)
- **Tenant Schemas**: Each tenant has its own schema (e.g., `default`, `acme`, `company2`)

### 2. **Domain-Based Routing**

The `TenantMainMiddleware` routes requests based on the **domain name**:

```
helpdesk-web-693i.onrender.com  →  Tenant: "default"  →  Schema: "default"
acme.example.com                →  Tenant: "acme"     →  Schema: "acme"
company2.example.com            →  Tenant: "company2" →  Schema: "company2"
```

### 3. **Data Isolation**

Each tenant schema has its own:
- Users (including admin users)
- Tickets
- Customers
- Knowledge Base articles
- SLA Policies
- All other tenant-specific data

**Important**: Users in one tenant **cannot** access data from another tenant. They're completely isolated.

## Current Setup

### Your Current Tenant

- **Domain**: `helpdesk-web-693i.onrender.com`
- **Schema Name**: `default`
- **Tenant Name**: `Default Tenant`
- **Admin User**: `root` (exists in the `default` schema only)

## How to Access Different Tenants

### Option 1: Different Domains (Production)

1. **Create a new tenant** via Django admin or management command:
   ```bash
   python manage.py create_tenant_custom \
     --schema_name acme \
     --name "ACME Corp" \
     --domain_url acme.example.com
   ```

2. **Point the domain** to your Render service (via DNS)

3. **Access**: `https://acme.example.com` → Routes to `acme` tenant

### Option 2: Subdomains (Development/Testing)

1. **Create tenant with subdomain**:
   ```bash
   python manage.py create_tenant_custom \
     --schema_name test \
     --name "Test Tenant" \
     --domain_url test.helpdesk-web-693i.onrender.com
   ```

2. **Access**: `https://test.helpdesk-web-693i.onrender.com` → Routes to `test` tenant

### Option 3: Local Development

For local development, you can use different ports or modify `/etc/hosts`:
```
127.0.0.1  acme.localhost
127.0.0.1  company2.localhost
```

## User Management Per Tenant

### Admin Users

Each tenant has its own admin users:
- `root` in `default` tenant → Can only access `default` tenant data
- `admin` in `acme` tenant → Can only access `acme` tenant data

### Creating Admin Users

**For the current tenant (`default`):**
- Already created: `root` / `varun16728...`
- Access: `https://helpdesk-web-693i.onrender.com/admin-login/`

**For a new tenant:**
1. Create the tenant first
2. Run the admin user creation command in that tenant's context:
   ```python
   from django_tenants.utils import tenant_context
   from tenants.models import Client
   
   tenant = Client.objects.get(schema_name='acme')
   with tenant_context(tenant):
       # Now create admin user in acme schema
       python manage.py create_admin_user --username admin --password secret123
   ```

## How to Differentiate Tenants

### In the Database

```sql
-- List all tenants
SELECT schema_name, name, domain_url FROM clients;

-- Switch to a tenant schema
SET search_path TO acme;

-- Query tenant-specific data
SELECT * FROM tickets;
```

### In Django Code

```python
from django_tenants.utils import get_tenant, tenant_context
from tenants.models import Client

# Get current tenant from request
tenant = get_tenant(request)
print(f"Current tenant: {tenant.name} (schema: {tenant.schema_name})")

# Access tenant-specific data (automatically scoped)
tickets = Ticket.objects.all()  # Only tickets from current tenant

# Switch to different tenant
acme_tenant = Client.objects.get(schema_name='acme')
with tenant_context(acme_tenant):
    tickets = Ticket.objects.all()  # Only tickets from acme tenant
```

### In the UI

You can display tenant information in your templates:
```django
{% if request.tenant %}
    <div>Tenant: {{ request.tenant.name }}</div>
    <div>Domain: {{ request.get_host }}</div>
{% endif %}
```

## Security Considerations

1. **Schema Isolation**: Data is automatically isolated - no cross-tenant access possible
2. **User Isolation**: Users in one tenant cannot log into another tenant
3. **Domain Routing**: Only domains registered in the `Domain` model can access a tenant
4. **Admin Access**: Each tenant has its own admin users

## Common Operations

### List All Tenants
```python
from tenants.models import Client
tenants = Client.objects.all()
for tenant in tenants:
    print(f"{tenant.name}: {tenant.schema_name} - {tenant.domain_url}")
```

### Create a New Tenant
```python
from tenants.models import Client, Domain

tenant = Client.objects.create(
    schema_name='newcompany',
    name='New Company',
    domain_url='newcompany.example.com'
)

Domain.objects.create(
    domain='newcompany.example.com',
    tenant=tenant,
    is_primary=True
)
```

### Access Tenant Data
```python
from django_tenants.utils import tenant_context
from tenants.models import Client

tenant = Client.objects.get(schema_name='acme')
with tenant_context(tenant):
    # All queries here are scoped to 'acme' schema
    tickets = Ticket.objects.all()
    users = User.objects.all()
```

## Troubleshooting

### "User does not exist" error
- Check which tenant schema you're in
- Users are tenant-specific - create user in the correct tenant

### "Tenant not found" error
- Check `Domain` model - domain must be registered
- Check `Client` model - tenant must exist
- Verify domain matches exactly (including subdomain)

### Cross-tenant data access
- This should never happen - django-tenants prevents it
- If you see data from another tenant, check your domain configuration

