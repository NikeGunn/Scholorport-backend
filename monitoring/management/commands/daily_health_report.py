"""
Daily Health Check Command
==========================
Runs comprehensive health checks and sends daily report via email/Slack.
Designed to be run via cron job or task scheduler.

Usage:
    python manage.py daily_health_report
    python manage.py daily_health_report --email-only
    python manage.py daily_health_report --slack-only
"""

from django.core.management.base import BaseCommand

from monitoring.health_check import health_service
from monitoring.slack_client import slack_client
from monitoring.email_client import email_client


class Command(BaseCommand):
    help = 'Run daily health check and send report via email/Slack'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-only',
            action='store_true',
            help='Send report via email only (skip Slack)',
        )
        parser.add_argument(
            '--slack-only',
            action='store_true',
            help='Send report via Slack only (skip email)',
        )
        parser.add_argument(
            '--no-notifications',
            action='store_true',
            help='Run health checks but don\'t send any notifications',
        )

    def handle(self, *args, **options):
        email_only = options['email_only']
        slack_only = options['slack_only']
        no_notifications = options['no_notifications']

        self.stdout.write('Running daily health check...\n')

        # Run comprehensive health checks
        summary = health_service.get_summary()

        self.stdout.write(f'Overall Status: {summary["overall_status"].upper()}')
        self.stdout.write(f'Healthy: {summary["stats"]["healthy"]} | Degraded: {summary["stats"]["degraded"]} | Unhealthy: {summary["stats"]["unhealthy"]}')

        if no_notifications:
            self.stdout.write('\nSkipping notifications as requested.')
            return

        # Send notifications
        email_sent = False
        slack_sent = False

        if not slack_only and email_client.enabled:
            self.stdout.write('\nSending email report...')
            email_sent = email_client.send_daily_report(summary)
            if email_sent:
                self.stdout.write(self.style.SUCCESS('✅ Email report sent'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to send email report'))

        if not email_only and slack_client.enabled:
            self.stdout.write('\nSending Slack report...')

            overall_status = summary['overall_status']
            stats = summary['stats']

            # Create Slack message
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌'
            }.get(overall_status, '📊')

            message = f"{status_emoji} Daily health report:\n• {stats['healthy']} healthy\n• {stats['degraded']} degraded\n• {stats['unhealthy']} unhealthy"

            color = {
                'healthy': 'success',
                'degraded': 'warning',
                'unhealthy': 'error'
            }.get(overall_status, 'info')

            slack_sent = slack_client.send_message(
                title="📊 Daily Health Report",
                message=message,
                color=color,
                fields=[
                    {"type": "mrkdwn", "text": f"*Overall Status:* `{overall_status.upper()}`"}
                ]
            )

            if slack_sent:
                self.stdout.write(self.style.SUCCESS('✅ Slack report sent'))
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to send Slack report'))

        # Summary
        self.stdout.write('\n' + '='*50)
        if email_sent or slack_sent:
            self.stdout.write(self.style.SUCCESS('Daily health report completed!'))
        else:
            self.stdout.write(self.style.WARNING('Health check completed, but no notifications were sent'))
        self.stdout.write('='*50)