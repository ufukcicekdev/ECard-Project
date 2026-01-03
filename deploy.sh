#!/bin/bash
# Deployment script for Railway

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec gunicorn ecard_project.wsgi:application -b 0.0.0.0:$PORT