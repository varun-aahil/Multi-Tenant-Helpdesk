#!/bin/bash
set -e

# Run migrations
echo "Running database migrations..."
python manage.py migrate_schemas

# Start the server
echo "Starting server..."
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -

