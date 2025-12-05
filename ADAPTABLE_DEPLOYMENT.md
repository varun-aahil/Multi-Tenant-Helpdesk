# Adaptable.io Deployment Guide (Free Tier - No Credit Card)

Adaptable offers free PostgreSQL and easy Django deployment!

## Step 1: Sign Up

1. Go to https://adaptable.io
2. Sign up with GitHub (no credit card needed)
3. Connect your GitHub repository

## Step 2: Create New App

1. Click "Create New App"
2. Select your repository
3. Choose "Python" → "Django"

## Step 3: Configure App

1. **App Name**: `helpdesk-app`
2. **Build Command**: (auto-detected)
3. **Start Command**: `gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT`

## Step 4: Add PostgreSQL Database

1. In app settings, click "Add Database"
2. Select "PostgreSQL"
3. Choose "Free" plan
4. Database will be automatically created

## Step 5: Add Redis (Optional)

Adaptable doesn't have built-in Redis, but you can:
- Use Upstash Redis (free tier): https://upstash.com
- Or skip Redis for now (Celery will work without it, just slower)

## Step 6: Environment Variables

Add these in Adaptable dashboard:
```
DATABASE_URL=<auto-set by Adaptable>
SECRET_KEY=<generate random key>
DJANGO_ENV=prod
ALLOWED_HOSTS=your-app.adaptable.app
REDIS_URL=<from Upstash if using>
```

## Step 7: Deploy

Click "Deploy" - Adaptable will:
1. Build your Dockerfile
2. Run migrations automatically
3. Start your app

## Step 8: Run Migrations (if needed)

Use Adaptable's console or SSH:
```bash
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
```

## Free Tier Limits

- 1 app
- 1 PostgreSQL database (1GB storage)
- 512MB RAM
- Apps may sleep after inactivity

## Recommendation

**Adaptable is probably the easiest free option** for Django with PostgreSQL!

