#!/bin/bash
# Deployment script for Railway

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Start the application
echo "Starting application..."
exec gunicorn ecard_project.wsgi:application -b 0.0.0.0:$PORT