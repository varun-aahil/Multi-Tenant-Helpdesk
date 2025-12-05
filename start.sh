#!/bin/bash

# Run migrations with verbose output
echo "=========================================="
echo "Running database migrations..."
echo "=========================================="
python manage.py migrate_schemas --verbosity=2
MIGRATION_EXIT_CODE=$?

if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "Migrations completed successfully!"
    echo "=========================================="
else
    echo "=========================================="
    echo "Migration exit code: $MIGRATION_EXIT_CODE"
    echo "Continuing anyway..."
    echo "=========================================="
fi

# Start the server
echo "=========================================="
echo "Starting Gunicorn server..."
echo "=========================================="
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -

