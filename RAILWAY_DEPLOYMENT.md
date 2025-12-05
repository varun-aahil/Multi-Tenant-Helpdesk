# Railway Deployment Guide

This guide will help you deploy your Multi-Tenant Helpdesk System to Railway for free.

## Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Your code pushed to GitHub

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your code is pushed to GitHub with:
- ✅ `Procfile` (for Railway to know how to start services)
- ✅ `requirements.txt` (with gunicorn included)
- ✅ All your Django code

### 2. Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository: `varun-aahil/Multi-Tenant-Helpdesk`
5. Railway will detect your project automatically

### 3. Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically create a PostgreSQL database
4. Note: Railway automatically sets `DATABASE_URL` environment variable

### 4. Add Redis Service

1. Click **"+ New"** again
2. Select **"Database"** → **"Add Redis"**
3. Railway will automatically create a Redis instance
4. Note: Railway automatically sets `REDIS_URL` environment variable

### 5. Configure Web Service

1. Railway should have detected your `Procfile` and created a web service
2. If not, click **"+ New"** → **"GitHub Repo"** → Select your repo
3. Click on the **web** service
4. Go to **"Settings"** tab
5. Set the following environment variables:

**Required Environment Variables:**

```
DJANGO_SETTINGS_MODULE=helpdesk_system.settings
DJANGO_ENV=prod
DEBUG=False
SECRET_KEY=<generate-a-random-secret-key>
ALLOWED_HOSTS=*.railway.app,your-custom-domain.com
```

**To generate SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Note:** Railway automatically provides:
- `DATABASE_URL` (from PostgreSQL service)
- `REDIS_URL` (from Redis service)
- `PORT` (for web server)

### 6. Configure Celery Worker Service

1. Click **"+ New"** → **"GitHub Repo"** → Select your repo
2. In the service settings, go to **"Settings"** → **"Deploy"**
3. Set **Start Command** to: `celery -A helpdesk_system worker --loglevel=info`
4. Set the same environment variables as web service:
   - `DJANGO_SETTINGS_MODULE=helpdesk_system.settings`
   - `DJANGO_ENV=prod`
   - `SECRET_KEY=<same-as-web-service>`
   - `DATABASE_URL` (will be auto-linked)
   - `REDIS_URL` (will be auto-linked)

### 7. Configure Celery Beat Service

1. Click **"+ New"** → **"GitHub Repo"** → Select your repo
2. In the service settings, go to **"Settings"** → **"Deploy"**
3. Set **Start Command** to: `celery -A helpdesk_system beat --loglevel=info`
4. Set the same environment variables as web service:
   - `DJANGO_SETTINGS_MODULE=helpdesk_system.settings`
   - `DJANGO_ENV=prod`
   - `SECRET_KEY=<same-as-web-service>`
   - `DATABASE_URL` (will be auto-linked)
   - `REDIS_URL` (will be auto-linked)

### 8. Link Services (Important!)

For each service (web, worker, beat):

1. Go to service **"Settings"** → **"Variables"**
2. Click **"New Variable"**
3. Add references to shared services:

**For DATABASE_URL:**
- Click **"Reference Variable"**
- Select your PostgreSQL service
- Select `DATABASE_URL`
- Variable name: `DATABASE_URL`

**For REDIS_URL:**
- Click **"Reference Variable"**
- Select your Redis service
- Select `REDIS_URL`
- Variable name: `REDIS_URL`

**Alternative:** Railway should auto-detect these, but if not, manually link them.

### 9. Deploy and Run Migrations

1. Railway will automatically deploy when you push to GitHub
2. Once deployed, click on your **web** service
3. Go to **"Deployments"** tab
4. Click on the latest deployment
5. Click **"View Logs"** to see deployment progress
6. Once running, click **"Settings"** → **"Generate Domain"** to get your app URL

### 10. Run Migrations

1. In Railway dashboard, click on your **web** service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Logs"** → **"Shell"** (or use Railway CLI)
5. Run:
   ```bash
   python manage.py migrate_schemas
   ```

### 11. Create Superuser

In the same shell:
```bash
python manage.py createsuperuser
```

### 12. Create Initial Tenant

In the same shell:
```bash
python manage.py shell
```

Then:
```python
from tenants.models import Client, Domain

tenant = Client(
    schema_name='acme',
    name='Acme Corporation',
    domain_url='acme.your-app.railway.app'  # Use your Railway domain
)
tenant.save()

domain = Domain(
    domain=tenant.domain_url,
    tenant=tenant,
    is_primary=True
)
domain.save()
```

## Troubleshooting

### Issue: "gunicorn not found"

**Solution:** Make sure `gunicorn==21.2.0` is in your `requirements.txt` (already added)

### Issue: Redis Connection Refused (Error 111)

**Solution:** 
1. Make sure Redis service is added and running
2. Make sure `REDIS_URL` is linked to all services (web, worker, beat)
3. Check that environment variables are set correctly

**To verify Redis connection:**
- Go to Redis service → Settings → Variables
- Copy the `REDIS_URL` value
- Make sure it's referenced in web, worker, and beat services

### Issue: Memory Full

**Solution:**
- Railway free tier has memory limits
- Try reducing services: You can run worker and beat in the same service temporarily
- Or upgrade to Railway Pro ($5/month)

### Issue: Database Connection Errors

**Solution:**
1. Make sure PostgreSQL service is added
2. Make sure `DATABASE_URL` is linked to all services
3. Wait for PostgreSQL to fully initialize (can take 1-2 minutes)

### Issue: Static Files Not Loading

**Solution:**
Add to web service build command (in Settings → Deploy):
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

### Issue: Services Keep Crashing

**Check logs:**
1. Click on the service
2. Go to "Deployments" → Latest deployment → "View Logs"
3. Look for error messages

**Common fixes:**
- Make sure all environment variables are set
- Make sure `SECRET_KEY` is set
- Make sure `ALLOWED_HOSTS` includes your Railway domain

## Railway CLI (Optional)

Install Railway CLI for easier management:

```bash
npm i -g @railway/cli
railway login
railway link  # Link to your project
railway run python manage.py migrate_schemas
```

## Cost Optimization

Railway free tier includes:
- $5 credit per month
- 500 hours of usage
- Limited memory

**To stay within free tier:**
1. Use smaller instance sizes
2. Consider running worker and beat together (less ideal but saves resources)
3. Monitor usage in Railway dashboard

## Next Steps

1. Set up custom domain (optional)
2. Configure email settings for notifications
3. Set up monitoring
4. Configure backups

## Quick Reference

**Service Commands:**
- Web: `gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT`
- Worker: `celery -A helpdesk_system worker --loglevel=info`
- Beat: `celery -A helpdesk_system beat --loglevel=info`

**Required Environment Variables:**
- `DJANGO_SETTINGS_MODULE=helpdesk_system.settings`
- `DJANGO_ENV=prod`
- `DEBUG=False`
- `SECRET_KEY=<your-secret-key>`
- `ALLOWED_HOSTS=*.railway.app`
- `DATABASE_URL` (auto-provided by Railway)
- `REDIS_URL` (auto-provided by Railway)

## Support

If you encounter issues:
1. Check Railway logs
2. Verify all environment variables are set
3. Ensure services are linked correctly
4. Check Railway status page: https://status.railway.app

