"""
Health Check Service for Scholarport
=====================================
Performs periodic health checks on all critical services and sends
Slack alerts when issues are detected.

Services monitored:
- Database connectivity
- External API availability (OpenAI, Firebase)
- Application response time
- Memory and disk usage
"""

import os
import time
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import lru_cache

from django.db import connection
from django.conf import settings

from .slack_client import slack_client

logger = logging.getLogger(__name__)


class HealthStatus:
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


class HealthCheckResult:
    """Result of a single health check"""

    def __init__(
        self,
        service: str,
        status: str,
        response_time: Optional[float] = None,
        message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        self.service = service
        self.status = status
        self.response_time = response_time  # in milliseconds
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service': self.service,
            'status': self.status,
            'response_time_ms': self.response_time,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class HealthCheckService:
    """
    Centralized health check service for monitoring all system components.

    Usage:
        from monitoring.health_check import health_service

        # Run all checks
        results = health_service.run_all_checks()

        # Run specific check
        db_health = health_service.check_database()
    """

    # Thresholds for determining health status
    THRESHOLDS = {
        'database': {
            'healthy_ms': 100,
            'degraded_ms': 500,
        },
        'api': {
            'healthy_ms': 1000,
            'degraded_ms': 3000,
        },
        'memory': {
            'healthy_percent': 70,
            'degraded_percent': 85,
        },
        'disk': {
            'healthy_percent': 70,
            'degraded_percent': 85,
        }
    }

    # Track previous statuses for change detection
    _previous_statuses: Dict[str, str] = {}
    _last_alert_time: Dict[str, datetime] = {}
    _alert_cooldown = timedelta(minutes=5)  # Minimum time between alerts for same service

    def __init__(self):
        self._checks_run = 0
        self._last_full_check = None

    def check_database(self) -> HealthCheckResult:
        """Check database connectivity and response time"""
        start_time = time.time()

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            thresholds = self.THRESHOLDS['database']
            if response_time < thresholds['healthy_ms']:
                status = HealthStatus.HEALTHY
                message = "Database responding normally"
            elif response_time < thresholds['degraded_ms']:
                status = HealthStatus.DEGRADED
                message = f"Database response slow ({response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = f"Database response very slow ({response_time:.0f}ms)"

            return HealthCheckResult(
                service='database',
                status=status,
                response_time=response_time,
                message=message,
                details={'query': 'SELECT 1'}
            )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                service='database',
                status=HealthStatus.UNHEALTHY,
                response_time=None,
                message=f"Database connection failed: {str(e)[:100]}",
                details={'error': str(e)}
            )

    def check_openai_api(self) -> HealthCheckResult:
        """Check OpenAI API availability"""
        import requests

        api_key = os.getenv('OPENAI_API_KEY', '')

        if not api_key:
            return HealthCheckResult(
                service='openai_api',
                status=HealthStatus.DEGRADED,
                message="OpenAI API key not configured"
            )

        start_time = time.time()

        try:
            # Just check the models endpoint which is lightweight
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                status = HealthStatus.HEALTHY if response_time < 2000 else HealthStatus.DEGRADED
                message = "OpenAI API responding"
            elif response.status_code == 401:
                status = HealthStatus.UNHEALTHY
                message = "OpenAI API authentication failed"
            elif response.status_code == 429:
                status = HealthStatus.DEGRADED
                message = "OpenAI API rate limited"
            else:
                status = HealthStatus.DEGRADED
                message = f"OpenAI API returned status {response.status_code}"

            return HealthCheckResult(
                service='openai_api',
                status=status,
                response_time=response_time,
                message=message
            )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service='openai_api',
                status=HealthStatus.DEGRADED,
                message="OpenAI API request timed out"
            )
        except Exception as e:
            return HealthCheckResult(
                service='openai_api',
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API check failed: {str(e)[:100]}"
            )

    def check_system_memory(self) -> HealthCheckResult:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent

            thresholds = self.THRESHOLDS['memory']
            if used_percent < thresholds['healthy_percent']:
                status = HealthStatus.HEALTHY
            elif used_percent < thresholds['degraded_percent']:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return HealthCheckResult(
                service='system_memory',
                status=status,
                message=f"Memory usage: {used_percent:.1f}%",
                details={
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent_used': used_percent
                }
            )
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return HealthCheckResult(
                service='system_memory',
                status=HealthStatus.DEGRADED,
                message=f"Could not check memory: {str(e)}"
            )

    def check_disk_space(self) -> HealthCheckResult:
        """Check disk space usage"""
        try:
            disk = psutil.disk_usage('/')
            used_percent = disk.percent

            thresholds = self.THRESHOLDS['disk']
            if used_percent < thresholds['healthy_percent']:
                status = HealthStatus.HEALTHY
            elif used_percent < thresholds['degraded_percent']:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return HealthCheckResult(
                service='disk_space',
                status=status,
                message=f"Disk usage: {used_percent:.1f}%",
                details={
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent_used': used_percent
                }
            )
        except Exception as e:
            logger.error(f"Disk check failed: {e}")
            return HealthCheckResult(
                service='disk_space',
                status=HealthStatus.DEGRADED,
                message=f"Could not check disk: {str(e)}"
            )

    def check_application_health(self) -> HealthCheckResult:
        """Check overall application health"""
        try:
            # Quick internal checks
            checks_passed = 0
            total_checks = 3
            issues = []

            # Check if we can import key modules
            try:
                from chat import views as chat_views
                checks_passed += 1
            except ImportError as e:
                issues.append(f"Chat module error: {e}")

            # Check if settings are properly loaded
            if hasattr(settings, 'INSTALLED_APPS'):
                checks_passed += 1
            else:
                issues.append("Settings not properly loaded")

            # Check environment
            if os.getenv('DJANGO_ENV'):
                checks_passed += 1
            else:
                issues.append("Environment not set")

            if checks_passed == total_checks:
                status = HealthStatus.HEALTHY
                message = "Application running normally"
            elif checks_passed > 0:
                status = HealthStatus.DEGRADED
                message = f"Some issues detected: {', '.join(issues)}"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Application has critical issues"

            return HealthCheckResult(
                service='application',
                status=status,
                message=message,
                details={
                    'checks_passed': checks_passed,
                    'total_checks': total_checks,
                    'issues': issues
                }
            )
        except Exception as e:
            return HealthCheckResult(
                service='application',
                status=HealthStatus.UNHEALTHY,
                message=f"Application health check failed: {str(e)}"
            )

    def run_all_checks(self, notify: bool = True) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks and optionally send Slack notifications.

        Args:
            notify: Whether to send Slack alerts for status changes

        Returns:
            Dictionary of service names to HealthCheckResult
        """
        results = {}

        # Run all checks
        checks = [
            self.check_database,
            self.check_openai_api,
            self.check_system_memory,
            self.check_disk_space,
            self.check_application_health,
        ]

        for check_func in checks:
            try:
                result = check_func()
                results[result.service] = result

                if notify:
                    self._handle_status_change(result)

            except Exception as e:
                logger.error(f"Health check {check_func.__name__} failed: {e}")
                results[check_func.__name__] = HealthCheckResult(
                    service=check_func.__name__,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}"
                )

        self._checks_run += 1
        self._last_full_check = datetime.utcnow()

        return results

    def _handle_status_change(self, result: HealthCheckResult):
        """Handle status changes and send alerts when appropriate"""
        previous_status = self._previous_statuses.get(result.service)
        current_status = result.status

        # Update previous status
        self._previous_statuses[result.service] = current_status

        # Check if we should send an alert
        should_alert = False

        # Alert on status degradation
        if previous_status is not None and previous_status != current_status:
            # Status changed
            if current_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
                should_alert = True
            # Also alert on recovery
            elif previous_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
                should_alert = True

        # First-time unhealthy should alert
        if previous_status is None and current_status == HealthStatus.UNHEALTHY:
            should_alert = True

        # Check cooldown
        last_alert = self._last_alert_time.get(result.service)
        if last_alert and datetime.utcnow() - last_alert < self._alert_cooldown:
            should_alert = False

        if should_alert:
            self._send_health_alert(result, previous_status)
            self._last_alert_time[result.service] = datetime.utcnow()

    def _send_health_alert(self, result: HealthCheckResult, previous_status: Optional[str]):
        """Send Slack alert for health check result"""
        # Determine if this is a recovery or degradation
        if previous_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY] and result.status == HealthStatus.HEALTHY:
            # Recovery
            title = f"✅ Service Recovered: {result.service}"
            message = f"Service `{result.service}` has recovered and is now healthy."
            color = 'success'
        else:
            # Degradation or new issue
            color = 'warning' if result.status == HealthStatus.DEGRADED else 'error'
            title = f"⚠️ Service Issue: {result.service}"
            message = result.message or f"Service `{result.service}` is {result.status}"

        slack_client.send_health_check_alert(
            service_name=result.service,
            status=result.status,
            response_time=result.response_time,
            details=message
        )

    def get_overall_status(self) -> str:
        """
        Get overall system health status based on all checks.

        Returns:
            'healthy', 'degraded', or 'unhealthy'
        """
        results = self.run_all_checks(notify=False)

        statuses = [r.status for r in results.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all health checks"""
        results = self.run_all_checks(notify=False)

        return {
            'overall_status': self.get_overall_status(),
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {name: result.to_dict() for name, result in results.items()},
            'stats': {
                'total_checks': len(results),
                'healthy': sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
                'degraded': sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED),
                'unhealthy': sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY),
            }
        }


# Singleton instance
health_service = HealthCheckService()
