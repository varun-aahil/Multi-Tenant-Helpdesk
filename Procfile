web: gunicorn helpdesk_system.wsgi:application --log-file -
worker: celery -A helpdesk_system worker --loglevel=info
beat: celery -A helpdesk_system beat --loglevel=info

