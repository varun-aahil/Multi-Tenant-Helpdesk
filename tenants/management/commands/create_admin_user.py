"""
Management command to create an admin user
Usage: python manage.py create_admin_user --username root --password varun16728... --email admin@example.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user with specified credentials'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Username for the admin user')
        parser.add_argument('--password', type=str, required=True, help='Password for the admin user')
        parser.add_argument('--email', type=str, default='', help='Email for the admin user (optional)')

    def handle(self, *args, **options):
        """Create the admin user"""
        username = options['username']
        password = options['password']
        email = options.get('email', '')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            if email:
                user.email = email
            user.save()
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  User "{username}" already exists. Updated password and admin privileges.'
                )
            )
        else:
            # Create new user
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created admin user: {username} (is_staff=True, is_superuser=True)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Admin user ready! You can now log in at /admin/ with:\n'
                f'   Username: {username}\n'
                f'   Password: {password}'
            )
        )

