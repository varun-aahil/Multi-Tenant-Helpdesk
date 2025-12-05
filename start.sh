#!/bin/bash

# Run migrations with verbose output
echo "=========================================="
echo "Step 1: Running shared schema migrations..."
echo "=========================================="
python manage.py migrate_schemas --shared --verbosity=2
SHARED_EXIT_CODE=$?

if [ $SHARED_EXIT_CODE -eq 0 ]; then
    echo "Shared schema migrations completed!"
else
    echo "Shared schema migration exit code: $SHARED_EXIT_CODE"
fi

echo ""
echo "=========================================="
echo "Step 2: Running all schema migrations..."
echo "=========================================="
python manage.py migrate_schemas --verbosity=2
MIGRATION_EXIT_CODE=$?

if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "All migrations completed successfully!"
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

