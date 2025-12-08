"""
Jobs/Careers App Views

API endpoints for job posting functionality.
Supports public job listings and admin CRUD operations.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes

from .models import Job
from .serializers import (
    JobSerializer,
    JobListSerializer,
    JobDetailSerializer,
    JobCreateSerializer,
    JobUpdateSerializer,
)


logger = logging.getLogger(__name__)


class JobPagination(LimitOffsetPagination):
    """
    Custom pagination for jobs using limit/offset.
    """
    default_limit = 20
    max_limit = 100


def paginate_jobs(queryset, request, serializer_class):
    """Helper function to paginate job querysets."""
    paginator = JobPagination()
    page = paginator.paginate_queryset(queryset, request)

    if page is not None:
        serializer = serializer_class(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True, context={'request': request})
    return Response(serializer.data)


def get_base_job_filters(request):
    """Extract common filter parameters from request."""
    filters = Q()

    # Filter by department
    department = request.query_params.get('department')
    if department:
        filters &= Q(department__iexact=department)

    # Filter by location
    location = request.query_params.get('location')
    if location:
        filters &= Q(location__icontains=location)

    # Filter by type
    job_type = request.query_params.get('type')
    if job_type:
        filters &= Q(type=job_type)

    # Filter by featured
    featured = request.query_params.get('featured')
    if featured:
        is_featured = featured.lower() in ('true', '1', 'yes')
        filters &= Q(is_featured=is_featured)

    # Search in title, description, requirements
    search = request.query_params.get('search')
    if search:
        filters &= (
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(requirements__icontains=search) |
            Q(responsibilities__icontains=search)
        )

    return filters


# ============================================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================================

@extend_schema(
    operation_id='jobs_list_active',
    tags=['Jobs'],
    summary='List all active jobs',
    description='''
    Get a list of all active job postings.

    **Filters:**
    - `department`: Filter by department name
    - `location`: Filter by location (partial match)
    - `type`: Filter by job type (full-time, part-time, contract, internship)
    - `featured`: Filter by featured status (true/false)
    - `search`: Search in title, description, requirements

    **Pagination:**
    - `limit`: Number of results per page (default: 20, max: 100)
    - `offset`: Number of results to skip

    **Notes:**
    - Only returns active jobs (is_active=true)
    - Excludes expired jobs (expires_at in the past)
    - Featured jobs appear first
    ''',
    parameters=[
        OpenApiParameter(
            name='department',
            type=str,
            description='Filter by department name',
            required=False
        ),
        OpenApiParameter(
            name='location',
            type=str,
            description='Filter by location',
            required=False
        ),
        OpenApiParameter(
            name='type',
            type=str,
            description='Filter by job type',
            enum=['full-time', 'part-time', 'contract', 'internship'],
            required=False
        ),
        OpenApiParameter(
            name='featured',
            type=bool,
            description='Filter by featured status',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=str,
            description='Search in title, description, requirements',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            description='Number of results per page',
            required=False
        ),
        OpenApiParameter(
            name='offset',
            type=int,
            description='Pagination offset',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=JobListSerializer(many=True),
            description='List of active jobs'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_jobs(request):
    """
    List all active jobs (public endpoint).
    Only returns active, non-expired jobs.
    """
    try:
        # Base query: only active jobs that haven't expired
        queryset = Job.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )

        # Apply filters
        filters = get_base_job_filters(request)
        if filters:
            queryset = queryset.filter(filters)

        # Order by featured first, then by posted_at
        queryset = queryset.order_by('-is_featured', '-posted_at', '-created_at')

        # Paginate and return
        return paginate_jobs(queryset, request, JobListSerializer)

    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return Response(
            {'detail': 'An error occurred while fetching jobs.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='jobs_get_by_slug',
    tags=['Jobs'],
    summary='Get job by slug',
    description='''
    Get detailed information about a specific job posting by its slug.

    **Notes:**
    - Only returns active, non-expired jobs
    - Returns 404 if job is inactive or expired
    ''',
    responses={
        200: OpenApiResponse(
            response=JobDetailSerializer,
            description='Job details'
        ),
        404: OpenApiResponse(description='Job not found or inactive')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_job_by_slug(request, slug):
    """
    Get job details by slug (public endpoint).
    Only returns the job if it's active and not expired.
    """
    try:
        # Get job by slug, must be active and not expired
        job = Job.objects.filter(
            slug=slug,
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).first()

        if not job:
            return Response(
                {'detail': 'Job not found or no longer available.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobDetailSerializer(job, context={'request': request})
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error getting job by slug {slug}: {str(e)}")
        return Response(
            {'detail': 'An error occurred while fetching the job.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
# ADMIN ENDPOINTS (Authentication Required)
# ============================================================

@extend_schema(
    operation_id='jobs_admin_list_all',
    tags=['Jobs Admin'],
    summary='List all jobs (Admin)',
    description='''
    Get all jobs including inactive ones (admin view).

    **Requires Authentication:** Yes (JWT Bearer token)

    **Additional Filters:**
    - `is_active`: Filter by active status (true/false)

    All other filters from public endpoint are also available.
    ''',
    parameters=[
        OpenApiParameter(
            name='is_active',
            type=bool,
            description='Filter by active status',
            required=False
        ),
        OpenApiParameter(
            name='department',
            type=str,
            description='Filter by department name',
            required=False
        ),
        OpenApiParameter(
            name='location',
            type=str,
            description='Filter by location',
            required=False
        ),
        OpenApiParameter(
            name='type',
            type=str,
            description='Filter by job type',
            enum=['full-time', 'part-time', 'contract', 'internship'],
            required=False
        ),
        OpenApiParameter(
            name='featured',
            type=bool,
            description='Filter by featured status',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=str,
            description='Search in title, description',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            description='Number of results per page',
            required=False
        ),
        OpenApiParameter(
            name='offset',
            type=int,
            description='Pagination offset',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=JobSerializer(many=True),
            description='List of all jobs'
        ),
        401: OpenApiResponse(description='Unauthorized')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_jobs(request):
    """
    List all jobs for admin (includes inactive jobs).
    Requires authentication.
    """
    try:
        # Start with all jobs
        queryset = Job.objects.all()

        # Apply common filters
        filters = get_base_job_filters(request)
        if filters:
            queryset = queryset.filter(filters)

        # Additional admin filter: is_active
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)

        # Order by featured first, then by created_at (newest first)
        queryset = queryset.order_by('-is_featured', '-created_at')

        # Paginate and return
        return paginate_jobs(queryset, request, JobSerializer)

    except Exception as e:
        logger.error(f"Error listing admin jobs: {str(e)}")
        return Response(
            {'detail': 'An error occurred while fetching jobs.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='jobs_admin_get_by_id',
    tags=['Jobs Admin'],
    summary='Get job by ID (Admin)',
    description='''
    Get job details by ID (admin view, includes inactive jobs).

    **Requires Authentication:** Yes (JWT Bearer token)
    ''',
    responses={
        200: OpenApiResponse(
            response=JobDetailSerializer,
            description='Job details'
        ),
        401: OpenApiResponse(description='Unauthorized'),
        404: OpenApiResponse(description='Job not found')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_job(request, job_id):
    """
    Get job details by ID (admin view).
    Can view both active and inactive jobs.
    """
    try:
        job = get_object_or_404(Job, id=job_id)
        serializer = JobDetailSerializer(job, context={'request': request})
        return Response(serializer.data)

    except Exception as e:
        if 'Job matching query does not exist' in str(e) or 'Not Found' in str(e):
            return Response(
                {'detail': 'Job not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        logger.error(f"Error getting job {job_id}: {str(e)}")
        return Response(
            {'detail': 'An error occurred while fetching the job.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='jobs_admin_create',
    tags=['Jobs Admin'],
    summary='Create a new job (Admin)',
    description='''
    Create a new job posting.

    **Requires Authentication:** Yes (JWT Bearer token)

    **Notes:**
    - `slug` is optional and will be auto-generated from title if not provided
    - `is_active` defaults to true
    - `is_featured` defaults to false
    - HTML content in description, requirements, responsibilities, and application_method is sanitized
    ''',
    request=JobCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=JobDetailSerializer,
            description='Job created successfully'
        ),
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Unauthorized')
    },
    examples=[
        OpenApiExample(
            'Create Job Example',
            value={
                'title': 'Senior Software Engineer',
                'department': 'Engineering',
                'location': 'Remote',
                'type': 'full-time',
                'description': '<p>We are looking for a senior software engineer...</p>',
                'requirements': '<ul><li>5+ years experience</li></ul>',
                'responsibilities': '<ul><li>Develop features</li></ul>',
                'application_email': 'careers@scholarport.co',
                'application_method': '<p>Please email your CV...</p>',
                'is_active': True,
                'is_featured': False,
                'expires_at': '2025-03-01T00:00:00Z'
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_create_job(request):
    """
    Create a new job posting.
    Requires authentication.
    """
    try:
        serializer = JobCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            job = serializer.save()
            response_serializer = JobDetailSerializer(job, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {'detail': 'Validation error', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return Response(
            {'detail': 'An error occurred while creating the job.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='jobs_admin_update',
    tags=['Jobs Admin'],
    summary='Update a job (Admin)',
    description='''
    Update an existing job posting. All fields are optional (partial update).

    **Requires Authentication:** Yes (JWT Bearer token)

    **Notes:**
    - All fields are optional for partial updates
    - If `slug` is provided empty, it will be regenerated from title
    - HTML content is sanitized on save
    ''',
    request=JobUpdateSerializer,
    responses={
        200: OpenApiResponse(
            response=JobDetailSerializer,
            description='Job updated successfully'
        ),
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Unauthorized'),
        404: OpenApiResponse(description='Job not found')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_job(request, job_id):
    """
    Update an existing job posting.
    Supports PATCH for partial updates.
    Requires authentication.
    """
    try:
        job = get_object_or_404(Job, id=job_id)

        serializer = JobUpdateSerializer(
            job,
            data=request.data,
            partial=True,  # Always allow partial updates
            context={'request': request}
        )

        if serializer.is_valid():
            job = serializer.save()
            response_serializer = JobDetailSerializer(job, context={'request': request})
            return Response(response_serializer.data)

        return Response(
            {'detail': 'Validation error', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        if 'Job matching query does not exist' in str(e) or 'Not Found' in str(e):
            return Response(
                {'detail': 'Job not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        logger.error(f"Error updating job {job_id}: {str(e)}")
        return Response(
            {'detail': 'An error occurred while updating the job.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id='jobs_admin_delete',
    tags=['Jobs Admin'],
    summary='Delete a job (Admin)',
    description='''
    Delete a job posting permanently.

    **Requires Authentication:** Yes (JWT Bearer token)
    ''',
    responses={
        204: OpenApiResponse(description='Job deleted successfully'),
        401: OpenApiResponse(description='Unauthorized'),
        404: OpenApiResponse(description='Job not found')
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_job(request, job_id):
    """
    Delete a job posting permanently.
    Requires authentication.
    """
    try:
        job = get_object_or_404(Job, id=job_id)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        if 'Job matching query does not exist' in str(e) or 'Not Found' in str(e):
            return Response(
                {'detail': 'Job not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        return Response(
            {'detail': 'An error occurred while deleting the job.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
