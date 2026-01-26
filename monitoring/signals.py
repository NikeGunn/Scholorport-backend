"""
Django Signals for Automatic Slack Notifications
=================================================
Automatically sends notifications for important events like:
- Server errors (500 errors)
- New user registrations
- Important data changes
"""

import logging
from django.dispatch import receiver
from django.core.signals import got_request_exception
from django.db.backends.signals import connection_created

from .slack_client import slack_client
from .email_client import email_client

logger = logging.getLogger(__name__)


# Track if we've sent a startup notification
_startup_notified = False


@receiver(connection_created)
def on_database_connection(sender, connection, **kwargs):
    """
    Called when a database connection is established.
    Send a startup notification once per application start.
    """
    global _startup_notified

    if not _startup_notified:
        _startup_notified = True
        try:
            import os
            env = os.getenv('DJANGO_ENV', 'development')

            # Only send startup notification in production
            if env == 'production':
                slack_client.send_message(
                    title="🚀 Application Started",
                    message="Scholarport backend has started successfully.",
                    color='success',
                    fields=[
                        {"type": "mrkdwn", "text": f"*Database:* Connected"},
                    ]
                )
        except Exception as e:
            logger.warning(f"Could not send startup notification: {e}")


@receiver(got_request_exception)
def handle_request_exception(sender, request, **kwargs):
    """
    Called when an unhandled exception occurs during request processing.
    Sends error notification to Slack.
    """
    import sys

    exc_info = sys.exc_info()
    if exc_info[0] is None:
        return

    exception = exc_info[1]

    # Don't notify for common non-critical errors
    skip_exceptions = (
        'Http404',
        'PermissionDenied',
        'SuspiciousOperation',
    )

    exc_name = type(exception).__name__
    if exc_name in skip_exceptions:
        return

    try:
        slack_client.send_error_alert(
            error=exception,
            request=request
        )
        # Also send email alert
        email_client.send_error_alert(
            error=exception,
            request=request
        )
    except Exception as e:
        # Don't let notification errors break the app
        logger.error(f"Failed to send error notifications: {e}")
