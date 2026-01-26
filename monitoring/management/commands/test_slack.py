"""
Django Management Command: Send Test Slack Notification
========================================================
Test the Slack integration by sending a test message.

Usage:
    python manage.py test_slack
"""

from django.core.management.base import BaseCommand

from monitoring.slack_client import slack_client


class Command(BaseCommand):
    help = 'Send a test Slack notification to verify integration'

    def handle(self, *args, **options):
        self.stdout.write('Sending test Slack notification...\n')

        if not slack_client.enabled:
            self.stdout.write(
                self.style.ERROR(
                    'Slack notifications are disabled!\n'
                    'Make sure SLACK_WEBHOOK_URL is set in your environment.\n'
                )
            )
            return

        success = slack_client.send_message(
            title="🧪 Test Notification",
            message="This is a test notification from Scholarport. If you see this, Slack integration is working correctly!",
            color='info',
            fields=[
                {"type": "mrkdwn", "text": "*Source:* `test_slack` command"},
            ],
            footer="This is a test message - no action required"
        )

        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Test notification sent successfully!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to send test notification. Check your webhook URL.')
            )
