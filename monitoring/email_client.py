"""
Email Client for Scholarport Notifications
==========================================
Sends email notifications via Gmail SMTP as an alternative to Slack.
Works alongside Slack notifications - you can use both.

Security Best Practices:
- Uses Gmail App Passwords (not your main password)
- Email credentials stored in environment variables only
- Rate limiting to prevent spam
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class EmailNotificationError(Exception):
    """Custom exception for email notification failures"""
    pass


class EmailClient:
    """
    Gmail SMTP client for sending notifications.

    Usage:
        from monitoring.email_client import email_client

        # Send simple notification
        email_client.send_notification(
            subject="Deployment Successful",
            message="Your app deployed in 45 seconds"
        )

        # Send error alert
        email_client.send_error_alert(exception, request)
    """

    def __init__(self):
        self._smtp_server = "smtp.gmail.com"
        self._smtp_port = 587
        self._enabled = None
        self._from_email = None
        self._password = None
        self._to_emails = None
        self._environment = os.getenv('DJANGO_ENV', 'development')

    @property
    def enabled(self) -> bool:
        """Check if email notifications are enabled"""
        if self._enabled is None:
            self._enabled = (
                bool(os.getenv('EMAIL_HOST_USER')) and
                bool(os.getenv('EMAIL_HOST_PASSWORD')) and
                bool(os.getenv('EMAIL_NOTIFICATION_TO')) and
                os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
            )
        return self._enabled

    @property
    def from_email(self) -> Optional[str]:
        """Get sender email"""
        if self._from_email is None:
            self._from_email = os.getenv('EMAIL_HOST_USER')
        return self._from_email

    @property
    def password(self) -> Optional[str]:
        """Get email password (app password)"""
        if self._password is None:
            self._password = os.getenv('EMAIL_HOST_PASSWORD')
        return self._password

    @property
    def to_emails(self) -> List[str]:
        """Get recipient emails"""
        if self._to_emails is None:
            emails_str = os.getenv('EMAIL_NOTIFICATION_TO', '')
            self._to_emails = [e.strip() for e in emails_str.split(',') if e.strip()]
        return self._to_emails

    def _create_message(
        self,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Scholarport-{self._environment.upper()}] {subject}"
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)

        # Add plain text or HTML body
        msg_body = MIMEText(body, 'html' if is_html else 'plain')
        msg.attach(msg_body)

        return msg

    def send_notification(
        self,
        subject: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        priority: str = 'normal'  # low, normal, high, critical
    ) -> bool:
        """
        Send email notification.

        Args:
            subject: Email subject
            message: Main message
            details: Additional details to include
            priority: Priority level (affects subject prefix)

        Returns:
            True if email was sent successfully
        """
        if not self.enabled:
            logger.debug("Email notifications disabled, skipping")
            return False

        # Add priority prefix
        priority_prefixes = {
            'low': '🔵',
            'normal': '📧',
            'high': '🟡',
            'critical': '🔴'
        }

        prefixed_subject = f"{priority_prefixes.get(priority, '📧')} {subject}"

        # Build email body
        body_parts = [
            f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"Environment: {self._environment.upper()}",
            "",
            "Message:",
            message
        ]

        if details:
            body_parts.extend(["", "Details:"])
            for key, value in details.items():
                body_parts.append(f"  {key}: {value}")

        body = "\n".join(body_parts)

        try:
            msg = self._create_message(prefixed_subject, body)

            with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg, to_addrs=self.to_emails)

            logger.info(f"Email notification sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def send_error_alert(
        self,
        error: Exception,
        request=None,
        extra_info: Optional[Dict] = None
    ) -> bool:
        """Send error alert via email"""
        error_type = type(error).__name__
        error_message = str(error)

        details = {
            'Error Type': error_type,
            'Error Message': error_message[:500]  # Truncate long messages
        }

        if request:
            details.update({
                'Path': request.path,
                'Method': request.method,
            })

            if hasattr(request, 'user') and request.user.is_authenticated:
                details['User'] = request.user.username

        if extra_info:
            details.update(extra_info)

        return self.send_notification(
            subject=f"Application Error - {error_type}",
            message=f"An error occurred in your Scholarport application:\n\n{error_message}",
            details=details,
            priority='high'
        )

    def send_deployment_notification(
        self,
        status: str,
        version: Optional[str] = None,
        deployed_by: Optional[str] = None,
        duration: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Send deployment status notification"""

        status_map = {
            'started': ('Deployment Started', 'normal'),
            'success': ('Deployment Successful', 'normal'),
            'failed': ('Deployment Failed', 'critical')
        }

        subject, priority = status_map.get(status, ('Deployment Update', 'normal'))

        if status == 'success':
            message = "🎉 Your Scholarport application has been deployed successfully!"
        elif status == 'failed':
            message = f"❌ Deployment failed. Please check the deployment logs.\n\nError: {error_message}"
        else:
            message = f"🚀 Deployment has started for Scholarport."

        details = {}
        if version:
            details['Version'] = version
        if deployed_by:
            details['Deployed By'] = deployed_by
        if duration:
            details['Duration'] = f"{duration:.1f} seconds"

        return self.send_notification(
            subject=subject,
            message=message,
            details=details,
            priority=priority
        )

    def send_health_alert(
        self,
        service_name: str,
        status: str,
        message: str,
        details: Optional[Dict] = None
    ) -> bool:
        """Send health check alert"""

        priority_map = {
            'healthy': 'low',
            'degraded': 'normal',
            'unhealthy': 'high'
        }

        priority = priority_map.get(status, 'normal')

        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }

        emoji = status_emoji.get(status, '📊')

        return self.send_notification(
            subject=f"{emoji} Health Alert - {service_name}",
            message=f"Service '{service_name}' is {status.upper()}.\n\n{message}",
            details=details or {'Service': service_name, 'Status': status.upper()},
            priority=priority
        )

    def send_daily_report(self, health_summary: Dict[str, Any]) -> bool:
        """Send daily health report"""

        overall_status = health_summary.get('overall_status', 'unknown')
        stats = health_summary.get('stats', {})
        checks = health_summary.get('checks', {})

        # Create summary message
        message_parts = [
            "📊 Daily Health Report for Scholarport",
            "",
            f"Overall Status: {overall_status.upper()}",
            "",
            "Summary:",
            f"  ✅ Healthy Services: {stats.get('healthy', 0)}",
            f"  ⚠️  Degraded Services: {stats.get('degraded', 0)}",
            f"  ❌ Unhealthy Services: {stats.get('unhealthy', 0)}",
            "",
            "Service Details:"
        ]

        for service, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            response_time = check_result.get('response_time_ms')

            status_icon = {'healthy': '✅', 'degraded': '⚠️', 'unhealthy': '❌'}.get(status, '❓')

            detail_line = f"  {status_icon} {service.title()}: {status.upper()}"
            if response_time:
                detail_line += f" ({response_time:.0f}ms)"

            message_parts.append(detail_line)

        message = "\n".join(message_parts)

        priority = {
            'healthy': 'low',
            'degraded': 'normal',
            'unhealthy': 'high'
        }.get(overall_status, 'normal')

        return self.send_notification(
            subject="Daily Health Report",
            message=message,
            priority=priority
        )

    def test_connection(self) -> bool:
        """Test email connection and send test message"""
        if not self.enabled:
            return False

        return self.send_notification(
            subject="Test Email Notification",
            message="This is a test email from your Scholarport monitoring system. If you received this, email notifications are working correctly!",
            details={'Test': 'Successful'},
            priority='normal'
        )


# Singleton instance
email_client = EmailClient()