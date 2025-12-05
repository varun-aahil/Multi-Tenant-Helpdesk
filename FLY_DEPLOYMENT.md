# Fly.io Deployment Guide

## Prerequisites

1. Install Fly.io CLI:
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Or download from: https://fly.io/docs/hands-on/install-flyctl/
   ```

2. Sign up for a free account: https://fly.io/app/sign-up

## Step 1: Login to Fly.io

```bash
flyctl auth login
```

## Step 2: Create PostgreSQL Database

```bash
flyctl postgres create --name helpdesk-db --region iad --vm-size shared-cpu-1x --volume-size 3
```

This will output a connection string. Save it!

## Step 3: Create Redis Instance

```bash
flyctl redis create --name helpdesk-redis --region iad --vm-size shared-cpu-1x
```

This will output a connection string. Save it!

## Step 4: Set Environment Variables

```bash
# Set database URL (from Step 2)
flyctl secrets set DATABASE_URL="postgresql://user:password@host:5432/dbname"

# Set Redis URL (from Step 3)
flyctl secrets set REDIS_URL="redis://host:6379"

# Set Django secret key
flyctl secrets set SECRET_KEY="your-secret-key-here"

# Set Django environment
flyctl secrets set DJANGO_ENV="prod"

# Set allowed hosts (will be set automatically after deployment)
flyctl secrets set ALLOWED_HOSTS="your-app-name.fly.dev"
```

## Step 5: Deploy the Application

```bash
# Launch the app (first time)
flyctl launch

# Or if already launched, deploy updates
flyctl deploy
```

## Step 6: Run Migrations

```bash
# Run migrations
flyctl ssh console -C "python manage.py migrate_schemas --shared"
flyctl ssh console -C "python manage.py migrate_schemas"
```

## Step 7: Create Superuser

```bash
flyctl ssh console -C "python manage.py createsuperuser"
```

## Step 8: Create a Tenant

```bash
flyctl ssh console -C "python manage.py create_tenant --schema_name acme --name 'Acme Corp' --domain acme.your-app-name.fly.dev"
```

## Step 9: Deploy Celery Worker (Optional)

Create a separate Fly.io app for the worker:

```bash
# Create a new app for worker
flyctl apps create helpdesk-worker

# Set the same secrets
flyctl secrets set -a helpdesk-worker DATABASE_URL="..."
flyctl secrets set -a helpdesk-worker REDIS_URL="..."
flyctl secrets set -a helpdesk-worker SECRET_KEY="..."
flyctl secrets set -a helpdesk-worker DJANGO_ENV="prod"

# Deploy worker with different CMD
flyctl deploy -a helpdesk-worker --config worker-fly.toml
```

## Troubleshooting

### View Logs
```bash
flyctl logs
```

### SSH into Container
```bash
flyctl ssh console
```

### Check App Status
```bash
flyctl status
```

### Scale Resources
```bash
flyctl scale vm shared-cpu-1x --memory 1024
```

## Free Tier Limits

- **3 shared-cpu-1x VMs** (256MB RAM each)
- **3GB persistent volume** for PostgreSQL
- **Up to 160GB outbound data transfer** per month
- Apps sleep after 5 minutes of inactivity (wake on request)

## Notes

- Fly.io automatically sets `PORT` environment variable
- Use `fly.toml` for app configuration
- Database and Redis are separate services
- Worker can be deployed as a separate app or use Fly.io's process groups

