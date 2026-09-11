#!/bin/sh
# Run collectstatic at startup so static files are available
# even when a bind mount overwrites the image's /app directory
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser if ADMIN_EMAIL and ADMIN_PASSWORD are set
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    python manage.py shell << END
from accounts.models import User
email = "$ADMIN_EMAIL"
password = "$ADMIN_PASSWORD"
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f"Admin user created: {email}")
else:
    print(f"Admin user already exists: {email}")
END
fi

exec "$@"
