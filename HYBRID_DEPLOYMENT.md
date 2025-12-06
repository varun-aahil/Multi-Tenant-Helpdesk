# Hybrid Deployment: Render (Web) + Free Celery Worker

Deploy your Django app on Render (free) and run Celery worker on a separate free service!

## Architecture

```
┌─────────────────┐         ┌──────────────┐
│  Render (Free)  │         │ Free Service │
│                 │         │              │
│  Django Web     │◄───────►│ Celery Worker│
│  PostgreSQL     │         │              │
│  Redis          │◄───────►│              │
└─────────────────┘         └──────────────┘
```

## Part 1: Deploy Main App on Render

Follow `RENDER_DEPLOYMENT.md` Steps 1-4 to set up:
- PostgreSQL database
- Redis instance
- Web service

**IMPORTANT:** For Redis, you'll need the **External Redis URL** (not Internal) so the external Celery worker can connect.

## Part 2: Deploy Celery Worker on Free Service

### Option 1: Railway (Free Tier - $5 Credit/Month)

Railway gives $5 free credit monthly, which should be enough for a low-concurrency Celery worker.

#### Setup Steps:

1. **Sign up at https://railway.app** (GitHub login, no credit card needed)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Service**
   - Railway auto-detects Dockerfile
   - Add environment variables:
     ```
     DATABASE_URL=<Render's External Database URL>
     REDIS_URL=<Render's External Redis URL>
     SECRET_KEY=<same as Render>
     DJANGO_ENV=prod
     CELERY_BROKER_URL=<Render's External Redis URL>
     CELERY_RESULT_BACKEND=<Render's External Redis URL>
     ```

4. **Set Start Command**
   - In Railway service settings, set:
     ```
     Start Command: celery -A helpdesk_system worker --beat --loglevel=info --concurrency=2
     ```

5. **Deploy**
   - Railway will build and deploy automatically
   - Check logs to ensure Celery connects to Render's Redis

#### Railway Free Tier:
- $5 credit/month
- 512MB RAM per service
- Should be enough for Celery worker with low concurrency

---

### Option 2: Koyeb (Free Tier)

Koyeb offers free tier with background workers.

#### Setup Steps:

1. **Sign up at https://www.koyeb.com** (GitHub login)

2. **Create App**
   - Click "Create App"
   - Connect GitHub repository
   - Select "Docker"

3. **Configure**
   - **Name**: `helpdesk-celery`
   - **Type**: Background Worker
   - **Start Command**: `celery -A helpdesk_system worker --beat --loglevel=info --concurrency=2`

4. **Environment Variables**:
   ```
   DATABASE_URL=<Render's External Database URL>
   REDIS_URL=<Render's External Redis URL>
   SECRET_KEY=<same as Render>
   DJANGO_ENV=prod
   CELERY_BROKER_URL=<Render's External Redis URL>
   CELERY_RESULT_BACKEND=<Render's External Redis URL>
   ```

5. **Deploy**

#### Koyeb Free Tier:
- 2 services
- 2GB RAM per service
- Global edge network
- No credit card required

---

### Option 3: Google Cloud Run (Free Tier)

Google Cloud Run has a generous free tier.

#### Setup Steps:

1. **Sign up at https://cloud.google.com** (no credit card for free tier)

2. **Install gcloud CLI**:
   ```bash
   # Windows
   # Download from: https://cloud.google.com/sdk/docs/install
   ```

3. **Create Dockerfile for Celery** (or reuse existing):
   ```dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
   COPY requirements.txt /app/
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . /app/
   CMD ["celery", "-A", "helpdesk_system", "worker", "--beat", "--loglevel=info", "--concurrency=2"]
   ```

4. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy helpdesk-celery \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DATABASE_URL=<Render's External Database URL> \
     --set-env-vars REDIS_URL=<Render's External Redis URL> \
     --set-env-vars SECRET_KEY=<same as Render> \
     --set-env-vars DJANGO_ENV=prod \
     --memory 512Mi \
     --cpu 1
   ```

#### Cloud Run Free Tier:
- 2 million requests/month
- 180,000 vCPU-seconds/month
- 360,000 GiB-seconds/month
- No credit card required

---

## Part 3: Get External URLs from Render

1. **External Database URL:**
   - Go to Render dashboard → PostgreSQL service
   - Copy "External Database URL" (not Internal)
   - Format: `postgresql://user:pass@host:5432/dbname`

2. **External Redis URL:**
   - Go to Render dashboard → Redis service
   - Copy "External Redis URL" (not Internal)
   - Format: `redis://host:6379` or `rediss://host:6379` (if SSL)

## Part 4: Verify Connection

1. **Check Celery Worker Logs:**
   - Should see: `Connected to redis://...`
   - Should see: `celery@hostname ready`

2. **Test from Django:**
   - In Render web service shell:
     ```python
     python manage.py shell
     >>> from tickets.tasks import your_task
     >>> your_task.delay()
     ```
   - Check Celery worker logs to see task execution

## Troubleshooting

### Celery can't connect to Redis
- Verify you're using **External Redis URL** (not Internal)
- Check if Redis allows external connections (Render's free Redis should)
- Check firewall/network settings

### Database connection errors
- Use **External Database URL** from Render
- Ensure database allows external connections
- Check DATABASE_URL format

### Tasks not executing
- Verify CELERY_BROKER_URL is set correctly
- Check Celery worker logs for errors
- Ensure worker is running: `celery -A helpdesk_system inspect active`

## Cost Summary

- **Render (Web + DB + Redis)**: FREE
- **Celery Worker (Railway)**: FREE ($5 credit/month)
- **Celery Worker (Koyeb)**: FREE
- **Celery Worker (Cloud Run)**: FREE (within limits)

**Total: $0/month! 🎉**

## Recommendation

**Start with Railway** - it's the easiest to set up and the $5/month credit should be plenty for a Celery worker with low concurrency.

