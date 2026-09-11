#!/bin/sh
# Run collectstatic at startup so static files are available
# even when a bind mount overwrites the image's /app directory
python manage.py collectstatic --noinput
exec "$@"
