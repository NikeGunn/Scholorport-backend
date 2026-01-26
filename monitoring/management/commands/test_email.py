"""
Test Email Notification Command
===============================
Send a test email to verify email integration is working.

Usage:
    python manage.py test_email
"""

from django.core.management.base import BaseCommand

from monitoring.email_client import email_client


class Command(BaseCommand):
    help = 'Send a test email notification to verify integration'

    def handle(self, *args, **options):
        self.stdout.write('Testing email notification...\n')

        if not email_client.enabled:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Email notifications are disabled!\n\n'
                    'Make sure these are set in your .env file:\n'
                    '  EMAIL_HOST_USER=your-gmail@gmail.com\n'
                    '  EMAIL_HOST_PASSWORD=your-app-password\n'
                    '  EMAIL_NOTIFICATION_TO=admin@yourcompany.com\n'
                    '  EMAIL_NOTIFICATIONS_ENABLED=true\n'
                )
            )
            return

        success = email_client.test_connection()

        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Test email sent successfully!')
            )
            self.stdout.write(f'Check your inbox: {", ".join(email_client.to_emails)}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to send test email. Check your email configuration.')
            )