# Setup Guide - Multi-Tenant Helpdesk

## Quick Start with Docker

1. **Clone and navigate to project**
```bash
cd "Multi-Tenant Helpdesk"
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your settings (optional for local dev)
```

3. **Build and start services**
```bash
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- Django web server (port 8000)
- Celery worker
- Celery beat scheduler

4. **Run migrations**
In a new terminal:
```bash
docker-compose exec web python manage.py migrate_schemas
```

5. **Create superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Create a tenant**
```bash
docker-compose exec web python manage.py create_tenant --schema_name acme --name "Acme Corp" --domain acme.localhost
```

7. **Access the application**
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/
- Tenant-specific: http://acme.localhost:8000/api/ (add to /etc/hosts or use domain mapping)

## Local Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis

### Steps

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL database**
```sql
CREATE DATABASE helpdesk_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE helpdesk_db TO postgres;
```

4. **Configure environment**
Create `.env` file:
```env
SECRET_KEY=your-secret-key
DJANGO_ENV=dev
DB_NAME=helpdesk_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

5. **Run migrations**
```bash
python manage.py migrate_schemas
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Create tenant**
```bash
python manage.py create_tenant --schema_name acme --name "Acme Corp" --domain acme.localhost
```

8. **Start development server**
```bash
python manage.py runserver
```

9. **Start Celery worker** (in separate terminal)
```bash
celery -A helpdesk_system worker --loglevel=info
```

10. **Start Celery beat** (in separate terminal)
```bash
celery -A helpdesk_system beat --loglevel=info
```

## Testing Tenant Isolation

1. Create multiple tenants:
```bash
python manage.py create_tenant --schema_name acme --name "Acme Corp" --domain acme.localhost
python manage.py create_tenant --schema_name beta --name "Beta Inc" --domain beta.localhost
```

2. Add to `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):
```
127.0.0.1 acme.localhost
127.0.0.1 beta.localhost
```

3. Access each tenant:
- http://acme.localhost:8000/api/tickets/
- http://beta.localhost:8000/api/tickets/

Each tenant will have isolated data.

## API Testing

### Using curl

1. **Create a ticket** (replace domain with your tenant domain):
```bash
curl -X POST http://acme.localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Ticket",
    "description": "This is a test ticket",
    "priority": "High",
    "customer_email": "customer@example.com",
    "customer_name": "John Doe"
  }'
```

2. **List tickets**:
```bash
curl http://acme.localhost:8000/api/tickets/
```

### Using Django Admin

1. Access http://localhost:8000/admin/
2. Login with superuser credentials
3. Switch tenant using the tenant selector in the admin interface
4. Manage tickets, customers, knowledge base, and SLA policies

## Troubleshooting

### Database connection errors
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists: `psql -U postgres -l`

### Tenant not found
- Ensure tenant exists: `python manage.py shell` → `Client.objects.all()`
- Check domain mapping in admin
- Verify `/etc/hosts` entries for local development

### Celery not working
- Ensure Redis is running: `redis-cli ping`
- Check Celery logs: `docker-compose logs celery`
- Verify task registration: `celery -A helpdesk_system inspect registered`

### Migration errors
- Run: `python manage.py migrate_schemas --shared`
- Then: `python manage.py migrate_schemas`

## Next Steps

1. Configure email settings in `.env` for production notifications
2. Set up SSL/TLS for production
3. Configure domain mapping for your tenants
4. Customize brand colors per tenant
5. Set up monitoring and logging

