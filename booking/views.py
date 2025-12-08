"""
Booking App Views

API endpoints for counselor session booking functionality.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes

from .models import (
    CounselorProfile,
    CounselorAvailability,
    BookingSession,
    BookingReminder
)
from .serializers import (
    CounselorProfileListSerializer,
    CounselorProfileDetailSerializer,
    CounselorProfileCreateUpdateSerializer,
    CounselorAvailabilitySerializer,
    BookingSessionListSerializer,
    BookingSessionDetailSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingCancelSerializer,
    BookingVerifySerializer,
    BookingFeedbackSerializer,
    AvailableSlotSerializer,
)


# ============================================================
# COUNSELOR ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Counselors'],
    summary='List all active counselors',
    description='Get a list of all counselors who are currently accepting bookings.',
    operation_id='counselors_list_all',
    parameters=[
        OpenApiParameter(
            name='specialization',
            type=str,
            description='Filter by specialization (partial match)',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=CounselorProfileListSerializer(many=True),
            description='List of counselors'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_counselors(request):
    """List all active counselors."""
    queryset = CounselorProfile.objects.filter(is_active=True)

    # Filter by specialization
    specialization = request.query_params.get('specialization')
    if specialization:
        queryset = queryset.filter(specializations__icontains=specialization)

    serializer = CounselorProfileListSerializer(
        queryset,
        many=True,
        context={'request': request}
    )
    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Counselors'],
    summary='Get counselor details',
    description='Get detailed information about a specific counselor including their availability.',
    operation_id='counselors_get_by_id',
    responses={
        200: OpenApiResponse(
            response=CounselorProfileDetailSerializer,
            description='Counselor details'
        ),
        404: OpenApiResponse(description='Counselor not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_counselor(request, counselor_id):
    """Get detailed counselor profile."""
    counselor = get_object_or_404(CounselorProfile, id=counselor_id, is_active=True)
    serializer = CounselorProfileDetailSerializer(
        counselor,
        context={'request': request}
    )
    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Counselors'],
    summary='Get counselor available slots',
    description='Get available booking slots for a counselor for the next N days.',
    parameters=[
        OpenApiParameter(
            name='days',
            type=int,
            description='Number of days to look ahead (default: 14, max: 90)',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=AvailableSlotSerializer(many=True),
            description='List of available time slots'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_counselor_slots(request, counselor_id):
    """Get available booking slots for a counselor."""
    counselor = get_object_or_404(CounselorProfile, id=counselor_id, is_active=True)

    days = min(int(request.query_params.get('days', 14)), 90)

    available_slots = []
    today = timezone.now().date()

    # Get all availabilities for this counselor
    availabilities = CounselorAvailability.objects.filter(
        counselor=counselor,
        is_available=True
    )

    # Get existing bookings
    existing_bookings = BookingSession.objects.filter(
        counselor=counselor,
        scheduled_date__gte=today,
        scheduled_date__lte=today + timedelta(days=days),
        status__in=['pending', 'confirmed']
    ).values_list('scheduled_date', 'scheduled_time')

    booked_slots = set((str(d), str(t)) for d, t in existing_bookings)

    for day_offset in range(days):
        check_date = today + timedelta(days=day_offset)
        weekday = check_date.weekday()

        # Check regular weekly availability
        for avail in availabilities.filter(weekday=weekday, specific_date__isnull=True):
            current_time = datetime.combine(check_date, avail.start_time)
            end_time = datetime.combine(check_date, avail.end_time)

            while current_time + timedelta(minutes=counselor.meeting_duration_minutes) <= end_time:
                slot_time = current_time.time()

                # Skip if already booked
                if (str(check_date), str(slot_time)) not in booked_slots:
                    # Skip if in the past
                    if check_date > today or (check_date == today and slot_time > timezone.now().time()):
                        available_slots.append({
                            'date': check_date,
                            'time': slot_time,
                            'counselor_id': counselor.id,
                            'counselor_name': counselor.full_name,
                            'duration_minutes': counselor.meeting_duration_minutes
                        })

                current_time += timedelta(minutes=counselor.meeting_duration_minutes)

        # Check specific date availability
        for avail in availabilities.filter(specific_date=check_date):
            current_time = datetime.combine(check_date, avail.start_time)
            end_time = datetime.combine(check_date, avail.end_time)

            while current_time + timedelta(minutes=counselor.meeting_duration_minutes) <= end_time:
                slot_time = current_time.time()

                if (str(check_date), str(slot_time)) not in booked_slots:
                    if check_date > today or (check_date == today and slot_time > timezone.now().time()):
                        available_slots.append({
                            'date': check_date,
                            'time': slot_time,
                            'counselor_id': counselor.id,
                            'counselor_name': counselor.full_name,
                            'duration_minutes': counselor.meeting_duration_minutes
                        })

                current_time += timedelta(minutes=counselor.meeting_duration_minutes)

    return Response({
        'success': True,
        'counselor': CounselorProfileListSerializer(counselor, context={'request': request}).data,
        'slots': available_slots
    })


# ============================================================
# BOOKING ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Booking'],
    summary='Create a new booking',
    description='''
    Book a consultation session with a counselor.

    **Flow:**
    1. Student fills form with name, email, phone, preferred date/time
    2. System creates booking with 'pending' status
    3. Verification email is sent to student
    4. Student clicks verification link to confirm
    5. Booking status changes to 'confirmed'

    **Note:** No login required. Email verification is used for security.
    ''',
    request=BookingCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=BookingSessionDetailSerializer,
            description='Booking created successfully',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'success': True,
                        'message': 'Booking created. Please check your email to verify.',
                        'data': {
                            'booking_id': '550e8400-e29b-41d4-a716-446655440000',
                            'student_name': 'John Doe',
                            'scheduled_date': '2024-01-15',
                            'scheduled_time': '10:00:00',
                            'status': 'pending'
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Validation error'),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_booking(request):
    """Create a new booking session."""
    serializer = BookingCreateSerializer(data=request.data)

    if serializer.is_valid():
        booking = serializer.save()

        # TODO: Send verification email
        # send_booking_verification_email(booking)

        response_serializer = BookingSessionDetailSerializer(
            booking,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Booking created successfully. Please check your email to verify.',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Booking'],
    summary='Get booking details',
    description='Get details of a specific booking by its UUID.',
    responses={
        200: OpenApiResponse(
            response=BookingSessionDetailSerializer,
            description='Booking details'
        ),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_booking(request, booking_id):
    """Get booking details by booking_id (UUID)."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)
    serializer = BookingSessionDetailSerializer(
        booking,
        context={'request': request}
    )
    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Booking'],
    summary='Update booking',
    description='Update booking details (reschedule, update notes, etc.)',
    request=BookingUpdateSerializer,
    responses={
        200: OpenApiResponse(
            response=BookingSessionDetailSerializer,
            description='Booking updated'
        ),
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def update_booking(request, booking_id):
    """Update an existing booking."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)

    # Can only update pending or confirmed bookings
    if booking.status not in ['pending', 'confirmed']:
        return Response({
            'success': False,
            'error': f"Cannot update a booking with status '{booking.status}'"
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = BookingUpdateSerializer(
        booking,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        # If date/time changed, mark as rescheduled
        if 'scheduled_date' in request.data or 'scheduled_time' in request.data:
            booking.status = 'rescheduled'

        serializer.save()

        response_serializer = BookingSessionDetailSerializer(
            booking,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Booking updated successfully',
            'data': response_serializer.data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Booking'],
    summary='Cancel booking',
    description='Cancel a booking. Must be at least 24 hours before scheduled time.',
    request=BookingCancelSerializer,
    responses={
        200: OpenApiResponse(description='Booking cancelled'),
        400: OpenApiResponse(description='Cannot cancel'),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_booking(request, booking_id):
    """Cancel a booking."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)

    serializer = BookingCancelSerializer(
        data=request.data,
        context={'booking': booking}
    )

    if serializer.is_valid():
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancelled_by = 'student'
        booking.cancellation_reason = serializer.validated_data.get('cancellation_reason', '')
        booking.save()

        # TODO: Send cancellation notification
        # send_booking_cancellation_email(booking)

        return Response({
            'success': True,
            'message': 'Booking cancelled successfully'
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Booking'],
    summary='Verify booking email',
    description='Verify booking using the token sent to email.',
    request=BookingVerifySerializer,
    responses={
        200: OpenApiResponse(description='Booking verified'),
        400: OpenApiResponse(description='Invalid token'),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_booking(request, booking_id):
    """Verify booking email."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)

    serializer = BookingVerifySerializer(data=request.data)

    if serializer.is_valid():
        token = serializer.validated_data['verification_token']

        if str(booking.verification_token) == str(token):
            booking.is_verified = True
            booking.status = 'confirmed'
            booking.confirmed_at = timezone.now()
            booking.save()

            # Create confirmation reminder record
            BookingReminder.objects.create(
                booking=booking,
                reminder_type='confirmation',
                sent_to=booking.student_email
            )

            return Response({
                'success': True,
                'message': 'Booking verified and confirmed successfully',
                'data': BookingSessionDetailSerializer(booking, context={'request': request}).data
            })
        else:
            return Response({
                'success': False,
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Booking'],
    summary='Submit booking feedback',
    description='Submit feedback and rating after a completed session.',
    request=BookingFeedbackSerializer,
    responses={
        200: OpenApiResponse(description='Feedback submitted'),
        400: OpenApiResponse(description='Cannot submit feedback'),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request, booking_id):
    """Submit post-session feedback."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)

    if booking.status != 'completed':
        return Response({
            'success': False,
            'error': 'Can only submit feedback for completed sessions'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = BookingFeedbackSerializer(
        booking,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()

        return Response({
            'success': True,
            'message': 'Thank you for your feedback!'
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Booking'],
    summary='Get bookings by email',
    description='Get all bookings for a specific email address.',
    parameters=[
        OpenApiParameter(
            name='email',
            type=str,
            description='Student email address',
            required=True
        ),
        OpenApiParameter(
            name='status',
            type=str,
            description='Filter by status',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=BookingSessionListSerializer(many=True),
            description='List of bookings'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_bookings_by_email(request):
    """Get all bookings for an email address."""
    email = request.query_params.get('email')

    if not email:
        return Response({
            'success': False,
            'error': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    queryset = BookingSession.objects.filter(student_email__iexact=email)

    # Filter by status
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    serializer = BookingSessionListSerializer(queryset, many=True)

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin'],
    summary='List all bookings (Admin)',
    description='Get all bookings with filtering options. Requires admin authentication.',
    parameters=[
        OpenApiParameter(name='status', type=str, required=False),
        OpenApiParameter(name='counselor_id', type=int, required=False),
        OpenApiParameter(name='date_from', type=str, required=False),
        OpenApiParameter(name='date_to', type=str, required=False),
    ],
    responses={
        200: OpenApiResponse(
            response=BookingSessionListSerializer(many=True),
            description='List of all bookings'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def admin_list_bookings(request):
    """Admin: List all bookings with filters."""
    queryset = BookingSession.objects.all()

    # Filters
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    counselor_id = request.query_params.get('counselor_id')
    if counselor_id:
        queryset = queryset.filter(counselor_id=counselor_id)

    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(scheduled_date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(scheduled_date__lte=date_to)

    serializer = BookingSessionListSerializer(queryset, many=True)

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin'],
    summary='Update booking status (Admin)',
    description='Update booking status (confirm, complete, mark no-show, etc.)',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'enum': ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']},
                'counselor_notes': {'type': 'string'}
            }
        }
    },
    responses={
        200: OpenApiResponse(description='Status updated'),
        404: OpenApiResponse(description='Booking not found')
    }
)
@api_view(['PATCH'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def admin_update_booking_status(request, booking_id):
    """Admin: Update booking status."""
    booking = get_object_or_404(BookingSession, booking_id=booking_id)

    new_status = request.data.get('status')
    if new_status:
        booking.status = new_status

        if new_status == 'confirmed' and not booking.confirmed_at:
            booking.confirmed_at = timezone.now()
        elif new_status == 'completed' and not booking.completed_at:
            booking.completed_at = timezone.now()
        elif new_status == 'cancelled' and not booking.cancelled_at:
            booking.cancelled_at = timezone.now()
            booking.cancelled_by = 'counselor'

    counselor_notes = request.data.get('counselor_notes')
    if counselor_notes:
        booking.counselor_notes = counselor_notes

    booking.save()

    return Response({
        'success': True,
        'message': f'Booking status updated to {booking.status}',
        'data': BookingSessionDetailSerializer(booking, context={'request': request}).data
    })


@extend_schema(
    tags=['Admin'],
    summary='Booking statistics',
    description='Get booking statistics for dashboard.',
    responses={
        200: OpenApiResponse(
            description='Booking statistics',
            examples=[
                OpenApiExample(
                    'Stats',
                    value={
                        'total_bookings': 150,
                        'pending': 10,
                        'confirmed': 25,
                        'completed': 100,
                        'cancelled': 15,
                        'today_bookings': 5,
                        'this_week_bookings': 20
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def booking_stats(request):
    """Get booking statistics."""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    total = BookingSession.objects.count()

    stats = {
        'total_bookings': total,
        'pending': BookingSession.objects.filter(status='pending').count(),
        'confirmed': BookingSession.objects.filter(status='confirmed').count(),
        'completed': BookingSession.objects.filter(status='completed').count(),
        'cancelled': BookingSession.objects.filter(status='cancelled').count(),
        'no_show': BookingSession.objects.filter(status='no_show').count(),
        'today_bookings': BookingSession.objects.filter(scheduled_date=today).count(),
        'this_week_bookings': BookingSession.objects.filter(
            scheduled_date__gte=week_start
        ).count(),
        'verified_rate': round(
            BookingSession.objects.filter(is_verified=True).count() / max(total, 1) * 100, 2
        ),
    }

    return Response({
        'success': True,
        'data': stats
    })


# ============================================================
# COUNSELOR AVAILABILITY MANAGEMENT (Admin)
# ============================================================

@extend_schema(
    tags=['Counselors'],
    summary='Set counselor availability',
    description='Add or update availability slots for a counselor.',
    request=CounselorAvailabilitySerializer,
    responses={
        201: OpenApiResponse(description='Availability created'),
        200: OpenApiResponse(description='Availability updated')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def set_counselor_availability(request, counselor_id):
    """Set availability for a counselor."""
    counselor = get_object_or_404(CounselorProfile, id=counselor_id)

    data = request.data.copy()

    serializer = CounselorAvailabilitySerializer(data=data)

    if serializer.is_valid():
        serializer.save(counselor=counselor)

        return Response({
            'success': True,
            'message': 'Availability set successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Counselors'],
    summary='Delete counselor availability',
    description='Remove an availability slot.',
    responses={
        200: OpenApiResponse(description='Availability deleted'),
        404: OpenApiResponse(description='Not found')
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])  # Change to IsAdminUser in production
def delete_counselor_availability(request, counselor_id, availability_id):
    """Delete an availability slot."""
    availability = get_object_or_404(
        CounselorAvailability,
        id=availability_id,
        counselor_id=counselor_id
    )

    availability.delete()

    return Response({
        'success': True,
        'message': 'Availability deleted successfully'
    })
