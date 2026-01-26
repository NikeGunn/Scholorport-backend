"""
Custom Django Middleware for Request Monitoring
================================================
Monitors all requests and sends alerts for:
- Server errors (500s)
- Slow responses
- High error rates
"""

import time
import logging
from collections import deque
from datetime import datetime, timedelta
from threading import Lock

from django.utils.deprecation import MiddlewareMixin

from .slack_client import slack_client
from .email_client import email_client

logger = logging.getLogger(__name__)


class RequestMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor request performance and errors.

    Features:
    - Tracks response times
    - Detects and alerts on 500 errors
    - Alerts on slow responses (configurable threshold)
    - Tracks error rate and alerts if too high
    """

    # Configuration
    SLOW_REQUEST_THRESHOLD_MS = 5000  # 5 seconds
    ERROR_RATE_THRESHOLD = 0.1  # 10% error rate
    ERROR_RATE_WINDOW = 100  # Last 100 requests

    # Shared state (thread-safe)
    _lock = Lock()
    _recent_requests = deque(maxlen=100)  # (timestamp, status_code, response_time)
    _last_error_rate_alert = None
    _error_rate_cooldown = timedelta(minutes=10)

    def process_request(self, request):
        """Mark the start time of the request"""
        request._monitoring_start_time = time.time()
        return None

    def process_response(self, request, response):
        """Monitor the response and send alerts if needed"""
        # Calculate response time
        start_time = getattr(request, '_monitoring_start_time', None)
        if start_time:
            response_time_ms = (time.time() - start_time) * 1000
        else:
            response_time_ms = 0

        status_code = response.status_code

        # Record this request
        self._record_request(status_code, response_time_ms)

        # Check for issues
        self._check_for_alerts(request, response, response_time_ms)

        return response

    def process_exception(self, request, exception):
        """Handle exceptions and send error alerts"""
        # Don't send alerts for 404s and similar
        from django.http import Http404
        from django.core.exceptions import PermissionDenied

        if isinstance(exception, (Http404, PermissionDenied)):
            return None

        # Send error alert for unexpected exceptions
        try:
            slack_client.send_error_alert(
                error=exception,
                request=request,
                extra_info={
                    'middleware': 'RequestMonitoringMiddleware'
                }
            )
            # Also send email alert
            email_client.send_error_alert(
                error=exception,
                request=request,
                extra_info={
                    'middleware': 'RequestMonitoringMiddleware'
                }
            )
        except Exception as e:
            logger.error(f"Failed to send alerts: {e}")

        return None

    def _record_request(self, status_code: int, response_time_ms: float):
        """Record request metrics (thread-safe)"""
        with self._lock:
            self._recent_requests.append({
                'timestamp': datetime.utcnow(),
                'status_code': status_code,
                'response_time_ms': response_time_ms,
            })

    def _check_for_alerts(self, request, response, response_time_ms: float):
        """Check if we need to send any alerts"""

        # Skip health check endpoints
        if '/health' in request.path:
            return

        status_code = response.status_code

        # Alert on 500 errors
        if status_code >= 500:
            self._alert_server_error(request, status_code, response_time_ms)

        # Alert on slow requests
        elif response_time_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            self._alert_slow_request(request, response_time_ms)

        # Check error rate periodically
        self._check_error_rate()

    def _alert_server_error(self, request, status_code: int, response_time_ms: float):
        """Send alert for server errors"""
        slack_client.send_message(
            title=f"Server Error ({status_code})",
            message=f"A server error occurred while processing a request.",
            color='error',
            fields=[
                {"type": "mrkdwn", "text": f"*Path:* `{request.path}`"},
                {"type": "mrkdwn", "text": f"*Method:* `{request.method}`"},
                {"type": "mrkdwn", "text": f"*Status:* `{status_code}`"},
                {"type": "mrkdwn", "text": f"*Response Time:* `{response_time_ms:.0f}ms`"},
            ]
        )

    def _alert_slow_request(self, request, response_time_ms: float):
        """Send alert for slow requests"""
        slack_client.send_message(
            title="Slow Request Detected",
            message=f"A request took longer than {self.SLOW_REQUEST_THRESHOLD_MS}ms to complete.",
            color='warning',
            fields=[
                {"type": "mrkdwn", "text": f"*Path:* `{request.path}`"},
                {"type": "mrkdwn", "text": f"*Method:* `{request.method}`"},
                {"type": "mrkdwn", "text": f"*Response Time:* `{response_time_ms:.0f}ms`"},
            ]
        )

    def _check_error_rate(self):
        """Check if error rate is too high"""
        with self._lock:
            if len(self._recent_requests) < 20:  # Need enough samples
                return

            errors = sum(1 for r in self._recent_requests if r['status_code'] >= 500)
            error_rate = errors / len(self._recent_requests)

            if error_rate > self.ERROR_RATE_THRESHOLD:
                # Check cooldown
                if (self._last_error_rate_alert and
                    datetime.utcnow() - self._last_error_rate_alert < self._error_rate_cooldown):
                    return

                self._last_error_rate_alert = datetime.utcnow()

                slack_client.send_critical_alert(
                    title="High Error Rate Detected",
                    description=f"Error rate is {error_rate*100:.1f}% over the last {len(self._recent_requests)} requests.",
                    affected_service="API"
                )
