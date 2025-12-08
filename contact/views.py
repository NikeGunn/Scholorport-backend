"""
Contact App Views

API endpoints for contact form submissions.
Public endpoint for form submission, admin endpoints for management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import ContactSubmission
from .serializers import (
    ContactSubmissionCreateSerializer,
    ContactSubmissionResponseSerializer,
    ContactSubmissionAdminSerializer,
    ContactSubmissionListSerializer,
)


# ============================================================
# PUBLIC ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Contact'],
    summary='Submit contact form',
    description='''
    Submit a contact form inquiry. No authentication required.

    **Form Fields:**
    - name: Full name (required)
    - email: Email address (required)
    - phone: Phone number (optional)
    - message: Message content (required, min 10 characters)
    - type: Inquiry type - 'student', 'university', 'agent', or 'other'
    ''',
    request=ContactSubmissionCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=ContactSubmissionResponseSerializer,
            description='Contact form submitted successfully',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'success': True,
                        'message': 'Thank you for contacting us! We will get back to you soon.',
                        'data': {
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'name': 'John Doe',
                            'email': 'john@example.com',
                            'created_at': '2024-01-15T10:30:00Z'
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact_form(request):
    """Submit a contact form (public endpoint)."""
    serializer = ContactSubmissionCreateSerializer(data=request.data)

    if serializer.is_valid():
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Save submission
        submission = serializer.save(
            ip_address=ip_address,
            user_agent=user_agent
        )

        response_serializer = ContactSubmissionResponseSerializer(submission)

        return Response({
            'success': True,
            'message': 'Thank you for contacting us! We will get back to you soon.',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin - Contact'],
    summary='List all contact submissions (Admin)',
    description='Get all contact submissions. Requires admin authentication.',
    operation_id='contact_admin_list_all',
    parameters=[
        OpenApiParameter(
            name='read',
            type=bool,
            description='Filter by read status',
            required=False
        ),
        OpenApiParameter(
            name='type',
            type=str,
            description="Filter by submission type ('student', 'university', 'agent', 'other')",
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=ContactSubmissionListSerializer(many=True),
            description='List of contact submissions'
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_submissions(request):
    """Admin: List all contact submissions."""
    queryset = ContactSubmission.objects.all()

    # Filter by read status
    read = request.query_params.get('read')
    if read is not None:
        if read.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(read=True)
        elif read.lower() in ['false', '0', 'no']:
            queryset = queryset.filter(read=False)

    # Filter by type
    submission_type = request.query_params.get('type')
    if submission_type in ['student', 'university', 'agent', 'other']:
        queryset = queryset.filter(type=submission_type)

    serializer = ContactSubmissionListSerializer(queryset, many=True)

    # Count stats
    unread_count = ContactSubmission.objects.filter(read=False).count()

    return Response({
        'success': True,
        'count': queryset.count(),
        'unread_count': unread_count,
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin - Contact'],
    summary='Get contact submission details (Admin)',
    description='Get full details of a contact submission. Requires admin authentication.',
    operation_id='contact_admin_get_by_id',
    responses={
        200: OpenApiResponse(
            response=ContactSubmissionAdminSerializer,
            description='Contact submission details'
        ),
        404: OpenApiResponse(description='Submission not found')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_get_submission(request, submission_id):
    """Admin: Get contact submission details."""
    submission = get_object_or_404(ContactSubmission, id=submission_id)
    serializer = ContactSubmissionAdminSerializer(submission)

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin - Contact'],
    summary='Mark submission as read (Admin)',
    description='Mark a contact submission as read. Requires admin authentication.',
    request=None,
    responses={
        200: OpenApiResponse(
            response=ContactSubmissionAdminSerializer,
            description='Submission marked as read'
        ),
        404: OpenApiResponse(description='Submission not found')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_mark_read(request, submission_id):
    """Admin: Mark submission as read."""
    submission = get_object_or_404(ContactSubmission, id=submission_id)
    submission.read = True
    submission.save()

    return Response({
        'success': True,
        'message': 'Submission marked as read',
        'data': ContactSubmissionAdminSerializer(submission).data
    })


@extend_schema(
    tags=['Admin - Contact'],
    summary='Update submission notes (Admin)',
    description='Update internal notes for a contact submission. Requires admin authentication.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'notes': {'type': 'string'},
                'read': {'type': 'boolean'}
            }
        }
    },
    responses={
        200: OpenApiResponse(description='Submission updated'),
        404: OpenApiResponse(description='Submission not found')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_update_submission(request, submission_id):
    """Admin: Update submission notes."""
    submission = get_object_or_404(ContactSubmission, id=submission_id)

    if 'notes' in request.data:
        submission.notes = request.data['notes']

    if 'read' in request.data:
        submission.read = request.data['read']

    submission.save()

    return Response({
        'success': True,
        'message': 'Submission updated',
        'data': ContactSubmissionAdminSerializer(submission).data
    })


@extend_schema(
    tags=['Admin - Contact'],
    summary='Delete submission (Admin)',
    description='Delete a contact submission. Requires admin authentication.',
    responses={
        200: OpenApiResponse(description='Submission deleted'),
        404: OpenApiResponse(description='Submission not found')
    }
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_submission(request, submission_id):
    """Admin: Delete a contact submission."""
    submission = get_object_or_404(ContactSubmission, id=submission_id)
    submission.delete()

    return Response({
        'success': True,
        'message': 'Submission deleted successfully'
    })


@extend_schema(
    tags=['Admin - Contact'],
    summary='Contact submission statistics (Admin)',
    description='Get statistics about contact submissions.',
    responses={
        200: OpenApiResponse(
            description='Contact statistics',
            examples=[
                OpenApiExample(
                    'Stats',
                    value={
                        'success': True,
                        'data': {
                            'total': 100,
                            'unread': 10,
                            'by_type': {
                                'student': 60,
                                'university': 20,
                                'agent': 15,
                                'other': 5
                            }
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """Admin: Get contact submission statistics."""
    total = ContactSubmission.objects.count()
    unread = ContactSubmission.objects.filter(read=False).count()

    by_type = {
        'student': ContactSubmission.objects.filter(type='student').count(),
        'university': ContactSubmission.objects.filter(type='university').count(),
        'agent': ContactSubmission.objects.filter(type='agent').count(),
        'other': ContactSubmission.objects.filter(type='other').count(),
    }

    return Response({
        'success': True,
        'data': {
            'total': total,
            'unread': unread,
            'by_type': by_type
        }
    })
