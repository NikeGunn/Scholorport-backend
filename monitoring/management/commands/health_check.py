"""
Django Management Command: Run Health Checks
=============================================
Manually run health checks and optionally send Slack notifications.

Usage:
    python manage.py health_check
    python manage.py health_check --notify
    python manage.py health_check --json
"""

import json
from django.core.management.base import BaseCommand

from monitoring.health_check import health_service


class Command(BaseCommand):
    help = 'Run system health checks and display results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send Slack notifications for health issues',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON',
        )

    def handle(self, *args, **options):
        notify = options['notify']
        output_json = options['json']

        self.stdout.write('Running health checks...\n')

        results = health_service.run_all_checks(notify=notify)

        if output_json:
            summary = health_service.get_summary()
            self.stdout.write(json.dumps(summary, indent=2))
        else:
            self.stdout.write('\n' + '='*50)
            self.stdout.write('HEALTH CHECK RESULTS')
            self.stdout.write('='*50 + '\n')

            for name, result in results.items():
                status_color = {
                    'healthy': self.style.SUCCESS,
                    'degraded': self.style.WARNING,
                    'unhealthy': self.style.ERROR,
                }

                color_func = status_color.get(result.status, self.style.NOTICE)
                status_str = color_func(f'[{result.status.upper()}]')

                self.stdout.write(f'{status_str} {name}')
                if result.message:
                    self.stdout.write(f'     {result.message}')
                if result.response_time:
                    self.stdout.write(f'     Response time: {result.response_time:.0f}ms')
                self.stdout.write('')

            overall = health_service.get_overall_status()
            self.stdout.write('='*50)
            overall_color = {
                'healthy': self.style.SUCCESS,
                'degraded': self.style.WARNING,
                'unhealthy': self.style.ERROR,
            }
            self.stdout.write(f'Overall Status: {overall_color[overall](overall.upper())}')
            self.stdout.write('='*50)
