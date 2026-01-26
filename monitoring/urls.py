"""
URL Configuration for Monitoring Module
"""

from django.urls import path
from .views import (
    HealthCheckView,
    DetailedHealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
)
from .admin_views import (
    TestSlackNotificationView,
    TriggerHealthCheckView,
)

app_name = 'monitoring'

urlpatterns = [
    # Simple health check (for load balancers, quick checks)
    path('health/', HealthCheckView.as_view(), name='health'),

    # Detailed health check (comprehensive status)
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='health-detailed'),

    # Kubernetes-style probes
    path('health/ready/', ReadinessCheckView.as_view(), name='readiness'),
    path('health/live/', LivenessCheckView.as_view(), name='liveness'),

    # Admin-only endpoints
    path('admin/test-slack/', TestSlackNotificationView.as_view(), name='test-slack'),
    path('admin/trigger-health-check/', TriggerHealthCheckView.as_view(), name='trigger-health-check'),
]
