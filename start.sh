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

