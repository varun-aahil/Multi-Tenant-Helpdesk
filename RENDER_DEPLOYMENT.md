# Render Deployment Guide (Free Tier - No Credit Card)

## Why Render Didn't Work Before

Render's free tier has some limitations:
- Services sleep after 15 minutes of inactivity
- Limited resources (512MB RAM)
- May need specific configuration

Let's fix the deployment!

## Step 1: Sign Up

1. Go to https://render.com
2. Sign up with GitHub (no credit card needed for free tier)
3. Connect your GitHub repository

## Step 2: Create PostgreSQL Database

1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - **Name**: `helpdesk-db`
   - **Database**: `helpdesk_db`
   - **User**: `helpdesk_user`
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click "Create Database"
5. **Save the Internal Database URL** (you'll need this)

## Step 3: Create Redis Instance

1. Click "New +"
2. Select "Redis"
3. Configure:
   - **Name**: `helpdesk-redis`
   - **Plan**: Free
4. Click "Create Redis"
5. **Save the Internal Redis URL**

## Step 4: Create Web Service

1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `helpdesk-web`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: (leave empty)
   - **Plan**: Free

5. **Environment Variables**:
   
   **Required:**
   ```
   DATABASE_URL=<from PostgreSQL service>
   REDIS_URL=<from Redis service>
   SECRET_KEY=<generate a random secret key>
   DJANGO_ENV=prod
   ALLOWED_HOSTS=helpdesk-web-693i.onrender.com
   ```
   
   **Optional (for tenant auto-creation):**
   ```
   DEFAULT_TENANT_DOMAIN=helpdesk-web-693i.onrender.com
   DEFAULT_TENANT_SCHEMA=default
   DEFAULT_TENANT_NAME=Default Tenant
   ```
   
   **Note:** If you don't set the optional variables, the startup script will automatically detect the domain from `ALLOWED_HOSTS` and create a tenant with default settings.
   
   **Important:** Replace `helpdesk-web-693i.onrender.com` with your actual Render domain!
   
   **Where to set environment variables in Render:**
   - After creating the service, go to the service dashboard
   - Click on "Environment" tab (or look for "Environment Variables" section)
   - Click "Add Environment Variable" or the "+" button
   - Add each variable one by one

6. Click "Create Web Service"

## Step 5: Celery Worker (Background Tasks)

**⚠️ IMPORTANT: Render's Background Workers are NOT free!** The cheapest plan is $7/month.

### Option 1: Skip Celery for Now (Free)
If you don't need background tasks immediately, you can skip this step. Your app will work, but:
- Scheduled tasks (like SLA checks) won't run automatically
- Email notifications might be delayed
- You can still use the app normally

### Option 2: Run Worker in Same Container (Free but Not Recommended)
You can modify your Dockerfile to run both web and worker, but this is not ideal:
- Uses more memory
- If one crashes, both crash
- Not production-ready

### Option 3: Deploy Celery on Separate Free Service (Recommended!)
**Best of both worlds!** Deploy your Django app on Render (free) and run Celery worker on Railway/Koyeb/Cloud Run (free). See `HYBRID_DEPLOYMENT.md` for complete guide.

### Option 4: Use Adaptable.io Instead
**Adaptable.io has a free tier** that might work better. See `ADAPTABLE_DEPLOYMENT.md`.

### Option 5: Pay for Render Worker ($7/month)
If you need Celery and want to use Render:
1. Click "New +"
2. Select "Background Worker"
3. Connect same GitHub repository
4. Configure:
   - **Name**: `helpdesk-worker`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Start Command**: `celery -A helpdesk_system worker --beat --loglevel=info --concurrency=2`
   - **Plan**: Starter ($7/month) - **No free tier available**

5. **Environment Variables** (same as web service):
   ```
   DATABASE_URL=<same as web>
   REDIS_URL=<same as web>
   SECRET_KEY=<same as web>
   DJANGO_ENV=prod
   ```

6. Click "Create Background Worker"

## Step 6: Run Migrations

After web service deploys:

1. Go to web service → "Shell"
2. Run:
   ```bash
   python manage.py migrate_schemas --shared
   python manage.py migrate_schemas
   ```

## Step 7: Default Tenant (Automatic!)

**Good news!** The app will automatically create a default tenant on startup.

The startup script will:
- Check if a tenant exists for your domain
- If not, automatically detect your domain from `ALLOWED_HOSTS` (or `DEFAULT_TENANT_DOMAIN` if set)
- Create a tenant with:
  - Schema name: `default` (or `DEFAULT_TENANT_SCHEMA` if set)
  - Name: `Default Tenant` (or `DEFAULT_TENANT_NAME` if set)
  - Domain: Your Render domain (auto-detected from `ALLOWED_HOSTS`)
- Run migrations on the tenant schema

**No shell access needed!** The script will automatically detect your domain from `ALLOWED_HOSTS` if you don't set the optional environment variables.

## Step 8: Create Superuser (Optional)

If you need a superuser, you can create one later when you have access, or skip this for now.

In the same shell:
```bash
python manage.py createsuperuser
```

**Note:** You'll need to create the superuser within the tenant context. After creating the tenant, you can create users normally.

## Important Notes

- **Free tier limitations**:
  - Services sleep after 15 min inactivity (first request wakes them up)
  - 512MB RAM per service
  - Limited CPU

- **If deployment fails**:
  - Check build logs for errors
  - Ensure DATABASE_URL and REDIS_URL use "Internal" URLs (not public)
  - Verify Dockerfile is correct

## Troubleshooting

### Service won't start
- Check environment variables are set correctly
- Verify DATABASE_URL format: `postgresql://user:pass@host:5432/dbname`
- Check logs in Render dashboard

### Database connection errors
- Use "Internal Database URL" not "External"
- Ensure database is in same region as web service

### Redis connection errors
- Use "Internal Redis URL"
- Check REDIS_URL format: `redis://host:6379`

