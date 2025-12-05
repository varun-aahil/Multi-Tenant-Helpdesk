#!/bin/bash
set -e

# Run migrations (don't fail if already migrated)
echo "Running database migrations..."
python manage.py migrate_schemas || echo "Migrations completed or failed, continuing..."

# Start the server
echo "Starting server..."
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -

