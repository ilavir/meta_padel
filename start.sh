#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Initialize database roles if not already done
# echo "Checking database initialization..."
# python init_db.py

# Start the application
echo "Starting application..."
exec gunicorn -b :5100 -w 1 --access-logfile - --error-logfile - tennis:app