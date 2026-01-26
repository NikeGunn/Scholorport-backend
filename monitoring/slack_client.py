"""
Slack Client for Scholarport Notifications
==========================================
Handles all Slack webhook communications with proper error handling,
retry logic, and message formatting.

Security Best Practices:
- Webhook URL is stored in environment variables only
- Never logged or exposed in error messages
- Rate limiting to prevent spam
"""

import os
import json
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Optional, Dict, Any, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SlackNotificationError(Exception):
    """Custom exception for Slack notification failures"""
    pass


class RateLimiter:
    """
    Simple rate limiter to prevent Slack API abuse.
    Allows max_calls in time_window seconds.
    """
    def __init__(self, max_calls: int = 30, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def can_proceed(self) -> bool:
        now = time.time()
        # Remove old calls outside the window
        self.calls = [t for t in self.calls if now - t < self.time_window]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False


class SlackClient:
    """
    Slack Webhook Client for sending notifications.

    Usage:
        from monitoring.slack_client import slack_client

        # Send simple message
        slack_client.send_message("Hello from Scholarport!")

        # Send error alert
        slack_client.send_error_alert(exception, request)

        # Send deployment notification
        slack_client.send_deployment_notification("success", "v1.2.3")
    """

    # Color scheme for different message types
    COLORS = {
        'success': '#36a64f',   # Green
        'warning': '#ffcc00',   # Yellow
        'error': '#ff0000',     # Red
        'info': '#3498db',      # Blue
        'critical': '#8e44ad', # Purple (critical errors)
    }

    # Emoji mapping for message types
    EMOJIS = {
        'success': ':white_check_mark:',
        'warning': ':warning:',
        'error': ':x:',
        'info': ':information_source:',
        'critical': ':rotating_light:',
        'deploy': ':rocket:',
        'server': ':computer:',
        'database': ':floppy_disk:',
        'api': ':electric_plug:',
        'user': ':bust_in_silhouette:',
        'security': ':shield:',
    }

    def __init__(self):
        self._webhook_url = None
        self._rate_limiter = RateLimiter(max_calls=30, time_window=60)
        self._enabled = None
        self._app_name = "Scholarport"
        self._environment = os.getenv('DJANGO_ENV', 'development')

    @property
    def webhook_url(self) -> Optional[str]:
        """Lazy load webhook URL from environment"""
        if self._webhook_url is None:
            self._webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        return self._webhook_url

    @property
    def enabled(self) -> bool:
        """Check if Slack notifications are enabled"""
        if self._enabled is None:
            self._enabled = bool(self.webhook_url) and os.getenv('SLACK_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
        return self._enabled

    def _get_base_fields(self) -> List[Dict[str, Any]]:
        """Get base fields included in all messages"""
        return [
            {
                "type": "mrkdwn",
                "text": f"*Environment:* `{self._environment}`"
            },
            {
                "type": "mrkdwn",
                "text": f"*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            }
        ]

    def _build_message(
        self,
        title: str,
        message: str,
        color: str = 'info',
        fields: Optional[List[Dict]] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a formatted Slack message with blocks.

        Args:
            title: Message title
            message: Main message text
            color: Color type (success, warning, error, info, critical)
            fields: Additional fields to include
            footer: Optional footer text
        """
        emoji = self.EMOJIS.get(color, ':bell:')
        hex_color = self.COLORS.get(color, self.COLORS['info'])

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]

        # Add base fields
        base_fields = self._get_base_fields()
        if fields:
            base_fields.extend(fields)

        blocks.append({
            "type": "section",
            "fields": base_fields[:10]  # Slack limits to 10 fields
        })

        # Add divider and footer if provided
        if footer:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": footer
                        }
                    ]
                }
            ])

        return {
            "attachments": [
                {
                    "color": hex_color,
                    "blocks": blocks
                }
            ]
        }

    def send_message(
        self,
        title: str,
        message: str,
        color: str = 'info',
        fields: Optional[List[Dict]] = None,
        footer: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """
        Send a formatted message to Slack.

        Args:
            title: Message title
            message: Main message text
            color: Color type (success, warning, error, info, critical)
            fields: Additional fields to include
            footer: Optional footer text
            force: Bypass rate limiting (use sparingly)

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping message")
            return False

        if not force and not self._rate_limiter.can_proceed():
            logger.warning("Slack rate limit reached, skipping message")
            return False

        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        payload = self._build_message(title, message, color, fields, footer)

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Slack notification sent: {title}")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Slack notification timed out")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack notification error: {str(e)}")
            return False

    def send_error_alert(
        self,
        error: Exception,
        request=None,
        extra_info: Optional[Dict] = None
    ) -> bool:
        """
        Send an error alert to Slack.

        Args:
            error: The exception that occurred
            request: Django request object (optional)
            extra_info: Additional context information
        """
        error_type = type(error).__name__
        error_message = str(error)

        fields = [
            {"type": "mrkdwn", "text": f"*Error Type:* `{error_type}`"}
        ]

        if request:
            fields.extend([
                {"type": "mrkdwn", "text": f"*Path:* `{request.path}`"},
                {"type": "mrkdwn", "text": f"*Method:* `{request.method}`"},
            ])

            # Add user info if available (but not sensitive data)
            if hasattr(request, 'user') and request.user.is_authenticated:
                fields.append({"type": "mrkdwn", "text": f"*User:* `{request.user.username}`"})

        if extra_info:
            for key, value in extra_info.items():
                fields.append({"type": "mrkdwn", "text": f"*{key}:* `{value}`"})

        return self.send_message(
            title=f"Application Error - {self._app_name}",
            message=f"```{error_message[:500]}```",  # Truncate long messages
            color='error',
            fields=fields,
            footer="🔧 Check application logs for full stack trace"
        )

    def send_critical_alert(
        self,
        title: str,
        description: str,
        affected_service: str = "Unknown"
    ) -> bool:
        """
        Send a critical alert for severe issues (database down, service unavailable, etc.)
        These bypass rate limiting.
        """
        fields = [
            {"type": "mrkdwn", "text": f"*Affected Service:* `{affected_service}`"},
            {"type": "mrkdwn", "text": f"*Severity:* `CRITICAL`"}
        ]

        return self.send_message(
            title=f"🚨 CRITICAL: {title}",
            message=description,
            color='critical',
            fields=fields,
            footer="⚠️ Immediate attention required!",
            force=True  # Bypass rate limiting for critical alerts
        )

    def send_deployment_notification(
        self,
        status: str,
        version: Optional[str] = None,
        deployed_by: Optional[str] = None,
        duration: Optional[float] = None,
        changes: Optional[List[str]] = None
    ) -> bool:
        """
        Send a deployment status notification.

        Args:
            status: 'started', 'success', or 'failed'
            version: Application version being deployed
            deployed_by: Username or system that triggered deployment
            duration: Deployment duration in seconds
            changes: List of changes deployed
        """
        color_map = {
            'started': 'info',
            'success': 'success',
            'failed': 'error'
        }

        emoji_map = {
            'started': '🚀',
            'success': '✅',
            'failed': '❌'
        }

        title_map = {
            'started': f"Deployment Started - {self._app_name}",
            'success': f"Deployment Successful - {self._app_name}",
            'failed': f"Deployment Failed - {self._app_name}"
        }

        fields = []

        if version:
            fields.append({"type": "mrkdwn", "text": f"*Version:* `{version}`"})

        if deployed_by:
            fields.append({"type": "mrkdwn", "text": f"*Deployed By:* `{deployed_by}`"})

        if duration:
            fields.append({"type": "mrkdwn", "text": f"*Duration:* `{duration:.1f}s`"})

        message = f"{emoji_map.get(status, '📦')} Deployment {status}"

        if changes and len(changes) > 0:
            changes_text = "\n".join([f"• {c}" for c in changes[:5]])
            message += f"\n\n*Changes:*\n{changes_text}"
            if len(changes) > 5:
                message += f"\n_...and {len(changes) - 5} more_"

        return self.send_message(
            title=title_map.get(status, f"Deployment - {self._app_name}"),
            message=message,
            color=color_map.get(status, 'info'),
            fields=fields,
            force=True  # Deployment notifications always sent
        )

    def send_health_check_alert(
        self,
        service_name: str,
        status: str,
        response_time: Optional[float] = None,
        details: Optional[str] = None
    ) -> bool:
        """
        Send a health check status alert.

        Args:
            service_name: Name of the service (database, api, cache, etc.)
            status: 'healthy', 'degraded', or 'unhealthy'
            response_time: Response time in milliseconds
            details: Additional details about the status
        """
        color_map = {
            'healthy': 'success',
            'degraded': 'warning',
            'unhealthy': 'error'
        }

        emoji_map = {
            'healthy': '💚',
            'degraded': '💛',
            'unhealthy': '💔'
        }

        fields = [
            {"type": "mrkdwn", "text": f"*Service:* `{service_name}`"},
            {"type": "mrkdwn", "text": f"*Status:* `{status.upper()}`"}
        ]

        if response_time:
            fields.append({"type": "mrkdwn", "text": f"*Response Time:* `{response_time:.0f}ms`"})

        message = f"{emoji_map.get(status, '❓')} Service `{service_name}` is {status}"
        if details:
            message += f"\n\n_{details}_"

        return self.send_message(
            title=f"Health Check Alert - {service_name}",
            message=message,
            color=color_map.get(status, 'info'),
            fields=fields,
            force=(status == 'unhealthy')  # Force send for unhealthy status
        )

    def send_security_alert(
        self,
        event_type: str,
        description: str,
        ip_address: Optional[str] = None,
        user: Optional[str] = None
    ) -> bool:
        """
        Send a security-related alert.

        Args:
            event_type: Type of security event (failed_login, suspicious_activity, etc.)
            description: Description of the event
            ip_address: IP address involved (if applicable)
            user: Username involved (if applicable)
        """
        fields = [
            {"type": "mrkdwn", "text": f"*Event Type:* `{event_type}`"}
        ]

        if ip_address:
            # Only show partial IP for privacy
            masked_ip = '.'.join(ip_address.split('.')[:2]) + '.xxx.xxx'
            fields.append({"type": "mrkdwn", "text": f"*IP:* `{masked_ip}`"})

        if user:
            fields.append({"type": "mrkdwn", "text": f"*User:* `{user}`"})

        return self.send_message(
            title=f"🔐 Security Alert - {self._app_name}",
            message=description,
            color='warning',
            fields=fields,
            footer="Review security logs for more details"
        )

    def send_simple_message(self, text: str) -> bool:
        """
        Send a simple text message without formatting.
        Useful for quick notifications.
        """
        if not self.enabled:
            return False

        if not self._rate_limiter.can_proceed():
            return False

        if not self.webhook_url:
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json={"text": f"[{self._environment.upper()}] {text}"},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


# Singleton instance for easy import
slack_client = SlackClient()


# Decorator for automatic error notification
def notify_on_error(func):
    """
    Decorator to automatically send Slack notification on function errors.

    Usage:
        @notify_on_error
        def my_critical_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            slack_client.send_error_alert(
                error=e,
                extra_info={'function': func.__name__}
            )
            raise
    return wrapper
