#!/bin/sh
# Collect static files
python manage.py collectstatic --noinput

# Run setup (migrations + admin user creation)
python manage.py setup_production

# Start gunicorn
exec "$@"
