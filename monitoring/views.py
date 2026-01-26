"""
API Views for Health Check Endpoints
=====================================
Provides endpoints for monitoring systems (like AWS health checks)
and manual health verification.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .health_check import health_service, HealthStatus


class HealthCheckView(APIView):
    """
    Simple health check endpoint for load balancers.
    Returns 200 if the application is running.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="health_check_simple",
        summary="Simple Health Check",
        description="Returns OK if the application is running. Used by load balancers.",
        responses={
            200: OpenApiResponse(description="Application is healthy"),
            503: OpenApiResponse(description="Application is unhealthy"),
        },
        tags=["Health"]
    )
    def get(self, request):
        return Response(
            {"status": "ok", "service": "scholarport"},
            status=status.HTTP_200_OK
        )


class DetailedHealthCheckView(APIView):
    """
    Detailed health check endpoint that checks all services.
    Returns comprehensive health status.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="health_check_detailed",
        summary="Detailed Health Check",
        description="Performs comprehensive health checks on all services including database, external APIs, and system resources.",
        responses={
            200: OpenApiResponse(description="All systems healthy"),
            503: OpenApiResponse(description="One or more systems unhealthy"),
        },
        tags=["Health"]
    )
    def get(self, request):
        # Run all health checks
        summary = health_service.get_summary()

        # Determine HTTP status based on overall health
        if summary['overall_status'] == HealthStatus.UNHEALTHY:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            http_status = status.HTTP_200_OK

        return Response(summary, status=http_status)


class ReadinessCheckView(APIView):
    """
    Kubernetes-style readiness probe.
    Returns 200 only if the application is ready to serve traffic.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="readiness_check",
        summary="Readiness Check",
        description="Checks if the application is ready to accept traffic. Used by Kubernetes/container orchestrators.",
        responses={
            200: OpenApiResponse(description="Application is ready"),
            503: OpenApiResponse(description="Application is not ready"),
        },
        tags=["Health"]
    )
    def get(self, request):
        # Check database connectivity (essential for readiness)
        db_result = health_service.check_database()

        if db_result.status == HealthStatus.UNHEALTHY:
            return Response(
                {
                    "status": "not_ready",
                    "reason": "database_unavailable",
                    "details": db_result.message
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(
            {"status": "ready"},
            status=status.HTTP_200_OK
        )


class LivenessCheckView(APIView):
    """
    Kubernetes-style liveness probe.
    Returns 200 if the application process is alive.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="liveness_check",
        summary="Liveness Check",
        description="Checks if the application process is alive. Used by Kubernetes/container orchestrators.",
        responses={
            200: OpenApiResponse(description="Application is alive"),
        },
        tags=["Health"]
    )
    def get(self, request):
        return Response(
            {"status": "alive"},
            status=status.HTTP_200_OK
        )
