#!/bin/bash
# Deployment script for Railway

# Install dependencies
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start the application
echo "Starting application..."
exec gunicorn ecard_project.wsgi:application -b 0.0.0.0:$PORT