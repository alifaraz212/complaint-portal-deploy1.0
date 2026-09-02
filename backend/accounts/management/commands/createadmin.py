"""
Management command to create an admin user.

Usage:
    python manage.py createadmin --email admin@example.com --password secret

- Sets role='admin' (application-level role)
- Sets is_staff=True (Django admin access)
- Sets is_superuser=True (full Django permissions)
- Idempotent: running again with same email does nothing
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create an admin user with the specified email and password."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True)
        parser.add_argument("--password", type=str, required=True)
        parser.add_argument("--full-name", type=str, default="Admin")

    def handle(self, *args, **options):
        email = options["email"].lower()
        password = options["password"]
        full_name = options["full_name"]

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"User with email '{email}' already exists. Skipping."
                )
            )
            return

        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters.")

        user = User.objects.create_superuser(
            email=email,
            password=password,
            full_name=full_name,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user created: {user.email} (role={user.role})"
            )
        )
