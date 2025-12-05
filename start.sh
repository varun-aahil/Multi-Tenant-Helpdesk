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
echo "Starting Gunicorn server..."
echo "=========================================="
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -

