"""
Admin Views for Monitoring
===========================
Protected endpoints for admins to manage monitoring.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .slack_client import slack_client
from .health_check import health_service


class TestSlackNotificationView(APIView):
    """
    Admin-only endpoint to test Slack notifications.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="test_slack_notification",
        summary="Test Slack Notification",
        description="Send a test notification to Slack. Admin access required.",
        responses={
            200: OpenApiResponse(description="Test notification sent"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin access required"),
            500: OpenApiResponse(description="Failed to send notification"),
        },
        tags=["Admin"]
    )
    def post(self, request):
        success = slack_client.send_message(
            title="🧪 Test Notification (Admin)",
            message=f"Test notification triggered by admin user `{request.user.username}`",
            color='info',
            fields=[
                {"type": "mrkdwn", "text": f"*Triggered By:* `{request.user.username}`"},
            ],
            footer="This is a test - no action required"
        )

        if success:
            return Response(
                {"status": "sent", "message": "Test notification sent to Slack"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"status": "failed", "message": "Failed to send notification. Check webhook configuration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TriggerHealthCheckView(APIView):
    """
    Admin-only endpoint to trigger health checks with notifications.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="trigger_health_check",
        summary="Trigger Health Check with Notifications",
        description="Run all health checks and send Slack alerts for any issues. Admin access required.",
        responses={
            200: OpenApiResponse(description="Health checks completed"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Admin access required"),
        },
        tags=["Admin"]
    )
    def post(self, request):
        # Run checks with notifications enabled
        results = health_service.run_all_checks(notify=True)
        summary = health_service.get_summary()

        return Response(
            {
                "status": "completed",
                "overall_status": summary['overall_status'],
                "stats": summary['stats'],
                "message": "Health checks completed. Notifications sent for any issues."
            },
            status=status.HTTP_200_OK
        )
