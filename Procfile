web: echo "=== Step 1: Shared migrations ===" && python manage.py migrate_schemas --shared --verbosity=2 && echo "=== Step 2: All migrations ===" && python manage.py migrate_schemas --verbosity=2 && echo "=== Starting server ===" && gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -
worker: celery -A helpdesk_system worker --beat --loglevel=info --concurrency=2

