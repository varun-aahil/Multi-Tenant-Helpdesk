web: gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -
worker: celery -A helpdesk_system worker --beat --loglevel=info

