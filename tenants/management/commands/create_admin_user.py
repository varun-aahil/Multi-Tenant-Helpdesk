"""
Management command to create an admin user
Usage: python manage.py create_admin_user --username root --password varun16728... --email admin@example.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, connection

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
        
        # Force create/update user - ensure it's committed
        try:
            user = User.objects.get(username=username)
            # User exists, update it
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            if email:
                user.email = email
            user.save()
            # Force commit by closing the connection
            connection.close()
            # Re-query to verify
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  User "{username}" already exists. Updated password and admin privileges.'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'   User details: is_staff={user.is_staff}, is_superuser={user.is_superuser}, is_active={user.is_active}'
                )
            )
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            # Force commit by closing the connection
            connection.close()
            # Re-query to verify
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created admin user: {username} (is_staff=True, is_superuser=True, is_active=True)'
                )
            )
        
        # Verify the user was created correctly and test authentication
        try:
            verify_user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Verification: User "{username}" exists with is_staff={verify_user.is_staff}, '
                    f'is_superuser={verify_user.is_superuser}, is_active={verify_user.is_active}'
                )
            )
            
            # Test authentication
            from django.contrib.auth import authenticate
            test_auth = authenticate(username=username, password=password)
            if test_auth:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Authentication test PASSED: User can authenticate with provided password'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Authentication test FAILED: User cannot authenticate with provided password!'
                    )
                )
                # Try to reset password again
                verify_user.set_password(password)
                verify_user.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Password reset attempted. Please try logging in again.'
                    )
                )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ ERROR: User "{username}" was not found after creation!'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Admin user ready! You can now log in at /admin-login/ with:\n'
                f'   Username: {username}\n'
                f'   Password: {password}'
            )
        )


