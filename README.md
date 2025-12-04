# Multi-Tenant Helpdesk System

A scalable SaaS platform that allows multiple distinct organizations (tenants) to manage support tickets within a secure, branded environment using a single deployment instance.

## Architecture

- **Pattern**: Shared Database, Isolated Schemas (django-tenants)
- **Framework**: Django 5.2.8 + Django REST Framework
- **Background Tasks**: Celery + Redis
- **Database**: PostgreSQL with schema isolation

## Features

- ✅ Multi-tenant architecture with schema isolation
- ✅ Ticket management with SLA tracking
- ✅ Knowledge Base articles
- ✅ Customer management
- ✅ Role-based access control (RBAC)
- ✅ SLA monitoring with automatic escalations
- ✅ Email notifications
- ✅ RESTful API with DRF

## Project Structure

```
├── helpdesk_system/          # Main project directory
│   ├── settings/             # Settings split by environment
│   │   ├── base.py          # Base settings
│   │   ├── dev.py           # Development settings
│   │   └── prod.py          # Production settings
│   ├── celery.py            # Celery configuration
│   └── exceptions.py        # Custom exception handler
├── tenants/                 # Tenant management (Public Schema)
├── tickets/                  # Ticket management (Tenant Schema)
├── knowledgebase/           # Knowledge Base (Tenant Schema)
├── customers/               # Customer management (Tenant Schema)
└── docker-compose.yml       # Docker services configuration
```

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)

### Installation

1. Clone the repository

2. Copy environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your configuration

4. Build and run with Docker:
```bash
docker-compose up --build
```

5. Run migrations:
```bash
docker-compose exec web python manage.py migrate_schemas
```

6. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

7. Create a tenant:
```bash
docker-compose exec web python manage.py shell
```

In the shell:
```python
from tenants.models import Client, Domain

# Create tenant
tenant = Client(schema_name='acme', name='Acme Corp', domain_url='acme.localhost')
tenant.save()

# Create domain
domain = Domain(domain=tenant.domain_url, tenant=tenant, is_primary=True)
domain.save()
```

## API Endpoints

### Tickets
- `GET /api/tickets/` - List tickets
- `POST /api/tickets/` - Create ticket
- `GET /api/tickets/{id}/` - Get ticket details
- `PUT /api/tickets/{id}/` - Update ticket
- `POST /api/tickets/{id}/assign/` - Assign ticket
- `POST /api/tickets/{id}/change_status/` - Change status
- `POST /api/tickets/{id}/force_close/` - Force close (Manager only)
- `GET /api/tickets/overdue/` - Get overdue tickets

### SLA Policies
- `GET /api/sla-policies/` - List SLA policies
- `POST /api/sla-policies/` - Create SLA policy

### Knowledge Base
- `GET /api/articles/` - List articles
- `POST /api/articles/` - Create article
- `GET /api/articles/{id}/` - Get article
- `POST /api/articles/{id}/increment_view/` - Increment view count

### Customers
- `GET /api/customers/` - List customers
- `POST /api/customers/` - Create customer
- `GET /api/customers/{id}/` - Get customer details

## Development

### Running Locally (without Docker)

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database

4. Run migrations:
```bash
python manage.py migrate_schemas
```

5. Run development server:
```bash
python manage.py runserver
```

6. Run Celery worker (in separate terminal):
```bash
celery -A helpdesk_system worker --loglevel=info
```

7. Run Celery beat (in separate terminal):
```bash
celery -A helpdesk_system beat --loglevel=info
```

## Testing

```bash
python manage.py test
```

## License

This project is part of a student project for SaaS Application / Backend Engineering.

