from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from django.core.management import call_command

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize admin user and fix migrations'

    def handle(self, *args, **options):
        # Drop existing tables if they exist
        with connection.cursor() as cursor:
            cursor.execute("""
                DO $$ 
                BEGIN
                    DROP TABLE IF EXISTS accounts_user_groups CASCADE;
                    DROP TABLE IF EXISTS accounts_user_user_permissions CASCADE;
                    DROP TABLE IF EXISTS accounts_user CASCADE;
                EXCEPTION WHEN others THEN
                    NULL;
                END $$;
            """)

        # Run migrations first
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=1)

        # Create superuser
        self.stdout.write('Creating superuser...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword123',
                first_name='Admin',
                last_name='User',
                user_type='admin',
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user')) 