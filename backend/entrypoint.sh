#!/bin/sh
set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Setting up admin user..."
python << 'PYTHON_EOF'
import os
import django
django.setup()

from accounts.models import User

admin_email = os.getenv('ADMIN_EMAIL')
admin_password = os.getenv('ADMIN_PASSWORD')

if admin_email and admin_password:
    if User.objects.filter(email=admin_email).exists():
        print(f"Admin user already exists: {admin_email}")
    else:
        User.objects.create_superuser(email=admin_email, password=admin_password)
        print(f"Admin user created successfully: {admin_email}")
else:
    print("ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping admin creation")
PYTHON_EOF

echo "Starting application..."
exec "$@"
