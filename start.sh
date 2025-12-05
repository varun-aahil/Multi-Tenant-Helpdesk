#!/bin/bash

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
" || echo "⚠️  Django configuration check failed"

echo ""
echo "=========================================="
echo "Starting Gunicorn server on port $PORT..."
echo "=========================================="
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file - --access-logfile - --error-logfile - --timeout 120

