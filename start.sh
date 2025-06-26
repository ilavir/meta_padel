#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Initialize application if not already done
# echo "Checking application initialization..."
# python init_app.py

# Start the application
echo "Starting application..."
exec gunicorn -b :5100 -w 2 --access-logfile - --error-logfile - tennis:app