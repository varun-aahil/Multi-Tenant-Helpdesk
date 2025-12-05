# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make start script executable
RUN chmod +x /app/start.sh

# Collect static files (for production)
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run migrations and start gunicorn directly
# This ensures the commands run even if Railway has issues with script execution
CMD /bin/bash -c "echo '=== CONTAINER STARTING ===' && \
python manage.py ensure_tables || echo 'ensure_tables skipped' && \
echo '=== Running shared migrations ===' && \
python manage.py migrate_schemas --shared --verbosity=2 && \
echo '=== Running all migrations ===' && \
python manage.py migrate_schemas --verbosity=2 && \
echo '=== Starting Gunicorn ===' && \
exec gunicorn helpdesk_system.wsgi:application --bind 0.0.0.0:${PORT:-8000} --log-file - --access-logfile - --error-logfile - --timeout 120"