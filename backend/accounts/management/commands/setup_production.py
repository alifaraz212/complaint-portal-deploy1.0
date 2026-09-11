from django.core.management.base import BaseCommand
from django.core.management import call_command
from accounts.models import User
import os


class Command(BaseCommand):
    help = 'Setup production: run migrations and create admin user'

    def handle(self, *args, **options):
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('Migrations completed'))

        # Create admin user if environment variables are set
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if admin_email and admin_password:
            if User.objects.filter(email=admin_email).exists():
                self.stdout.write(f'Admin user already exists: {admin_email}')
            else:
                User.objects.create_superuser(email=admin_email, password=admin_password)
                self.stdout.write(
                    self.style.SUCCESS(f'Admin user created: {admin_email}')
                )
        else:
            self.stdout.write('ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping admin creation')
