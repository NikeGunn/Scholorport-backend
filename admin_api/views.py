"""
Admin API Views

Comprehensive API endpoints for React admin panel.
Includes authentication, dashboard, and data management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from .serializers import (
    AdminLoginSerializer,
    AdminUserSerializer,
    AdminUserListSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
)

# Import models from other apps
from chat.models import ConversationSession, ChatMessage, University, StudentProfile
from booking.models import CounselorProfile, BookingSession
from blog.models import BlogPost, BlogCategory, BlogComment, BlogSubscription
from partners.models import Partner
from contact.models import ContactSubmission


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin Auth'],
    summary='Admin Login',
    description='''
    Authenticate an admin user and get JWT tokens.

    **Requirements:**
    - User must have `is_staff=True` (admin privileges)
    - User must be active (`is_active=True`)

    **Returns:**
    - `access`: JWT access token (use in Authorization header)
    - `refresh`: JWT refresh token (use to get new access token)
    - `user`: Admin user profile data

    **Usage:**
    ```
    Authorization: Bearer <access_token>
    ```
    ''',
    request=AdminLoginSerializer,
    responses={
        200: OpenApiResponse(
            description='Login successful',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'success': True,
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {
                            'id': 1,
                            'username': 'admin',
                            'email': 'admin@scholarport.co',
                            'full_name': 'Admin User',
                            'role': 'superadmin'
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid credentials'),
        403: OpenApiResponse(description='Not an admin user')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Admin login endpoint."""
    serializer = AdminLoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': AdminUserSerializer(user).data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Auth'],
    summary='Get Current Admin User',
    description='Get the profile of the currently authenticated admin user.',
    responses={
        200: OpenApiResponse(response=AdminUserSerializer),
        401: OpenApiResponse(description='Not authenticated')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_current_user(request):
    """Get current authenticated admin user."""
    serializer = AdminUserSerializer(request.user)
    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin Auth'],
    summary='Update Admin Profile',
    description='Update the profile of the currently authenticated admin user.',
    request=AdminUserUpdateSerializer,
    responses={
        200: OpenApiResponse(response=AdminUserSerializer),
        400: OpenApiResponse(description='Validation error')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_profile(request):
    """Update current admin user profile."""
    serializer = AdminUserUpdateSerializer(
        request.user,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': AdminUserSerializer(request.user).data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Auth'],
    summary='Change Password',
    description='Change the password of the currently authenticated admin user.',
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description='Password changed successfully'),
        400: OpenApiResponse(description='Invalid password')
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def change_password(request):
    """Change current user's password."""
    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'success': False,
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Auth'],
    summary='Logout',
    description='Logout and blacklist the refresh token.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'Refresh token to blacklist'}
            }
        }
    },
    responses={
        200: OpenApiResponse(description='Logged out successfully'),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_logout(request):
    """Logout and blacklist refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass  # Token might already be blacklisted or invalid

    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })


# ============================================================
# DASHBOARD ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get Dashboard Overview',
    description='''
    Get comprehensive dashboard statistics for the admin panel.

    **Includes:**
    - Total counts for all entities
    - Recent activity metrics
    - Trend data (today, this week, this month)
    ''',
    responses={
        200: OpenApiResponse(
            description='Dashboard data',
            examples=[
                OpenApiExample(
                    'Dashboard Stats',
                    value={
                        'success': True,
                        'data': {
                            'conversations': {'total': 150, 'completed': 120, 'today': 5},
                            'bookings': {'total': 50, 'pending': 10, 'confirmed': 30},
                            'blog': {'posts': 20, 'views': 5000, 'comments': 100},
                            'users': {'total': 500, 'new_today': 10},
                            'partners': {'total': 15, 'universities': 10, 'agents': 5},
                            'contact': {'total': 25, 'unread': 5}
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_overview(request):
    """Get dashboard overview statistics."""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Conversations stats
    total_conversations = ConversationSession.objects.count()
    completed_conversations = ConversationSession.objects.filter(is_completed=True).count()
    today_conversations = ConversationSession.objects.filter(
        created_at__date=today
    ).count()

    # Bookings stats
    total_bookings = BookingSession.objects.count()
    pending_bookings = BookingSession.objects.filter(status='pending').count()
    confirmed_bookings = BookingSession.objects.filter(status='confirmed').count()
    today_bookings = BookingSession.objects.filter(
        created_at__date=today
    ).count()

    # Blog stats
    total_posts = BlogPost.objects.filter(is_deleted=False).count()
    published_posts = BlogPost.objects.filter(status='published', is_deleted=False).count()
    total_views = BlogPost.objects.filter(is_deleted=False).aggregate(
        total=Sum('view_count')
    )['total'] or 0
    pending_comments = BlogComment.objects.filter(status='pending').count()

    # Users stats
    total_profiles = StudentProfile.objects.count()
    today_profiles = StudentProfile.objects.filter(
        created_at__date=today
    ).count()

    # Partners stats
    total_partners = Partner.objects.filter(is_active=True).count()
    university_partners = Partner.objects.filter(type='university', is_active=True).count()
    agent_partners = Partner.objects.filter(type='agent', is_active=True).count()

    # Contact stats
    total_contacts = ContactSubmission.objects.count()
    unread_contacts = ContactSubmission.objects.filter(read=False).count()
    today_contacts = ContactSubmission.objects.filter(
        created_at__date=today
    ).count()

    # Counselors stats
    total_counselors = CounselorProfile.objects.filter(is_active=True).count()

    return Response({
        'success': True,
        'data': {
            'conversations': {
                'total': total_conversations,
                'completed': completed_conversations,
                'completion_rate': round((completed_conversations / max(total_conversations, 1)) * 100, 1),
                'today': today_conversations
            },
            'bookings': {
                'total': total_bookings,
                'pending': pending_bookings,
                'confirmed': confirmed_bookings,
                'today': today_bookings
            },
            'blog': {
                'total_posts': total_posts,
                'published': published_posts,
                'total_views': total_views,
                'pending_comments': pending_comments
            },
            'students': {
                'total': total_profiles,
                'today': today_profiles
            },
            'partners': {
                'total': total_partners,
                'universities': university_partners,
                'agents': agent_partners
            },
            'contact': {
                'total': total_contacts,
                'unread': unread_contacts,
                'today': today_contacts
            },
            'counselors': {
                'total': total_counselors
            },
            'timestamp': timezone.now().isoformat()
        }
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get Recent Activity',
    description='Get recent activity across all modules.',
    parameters=[
        OpenApiParameter(name='limit', type=int, description='Number of items per category (default: 5)')
    ],
    responses={
        200: OpenApiResponse(description='Recent activity data')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def recent_activity(request):
    """Get recent activity across all modules."""
    limit = int(request.query_params.get('limit', 5))

    # Recent conversations
    recent_conversations = ConversationSession.objects.order_by('-created_at')[:limit]
    conversations_data = [{
        'id': str(c.session_id),
        'completed': c.is_completed,
        'step': c.current_step,
        'created_at': c.created_at.isoformat()
    } for c in recent_conversations]

    # Recent bookings
    recent_bookings = BookingSession.objects.order_by('-created_at')[:limit]
    bookings_data = [{
        'id': str(b.booking_id),
        'student_name': b.student_name,
        'status': b.status,
        'scheduled_date': str(b.scheduled_date),
        'created_at': b.created_at.isoformat()
    } for b in recent_bookings]

    # Recent contact submissions
    recent_contacts = ContactSubmission.objects.order_by('-created_at')[:limit]
    contacts_data = [{
        'id': str(c.id),
        'name': c.name,
        'email': c.email,
        'type': c.type,
        'read': c.read,
        'created_at': c.created_at.isoformat()
    } for c in recent_contacts]

    # Recent blog comments
    recent_comments = BlogComment.objects.order_by('-created_at')[:limit]
    comments_data = [{
        'id': str(c.comment_id),
        'author': c.author_name,
        'post_title': c.post.title[:50],
        'status': c.status,
        'created_at': c.created_at.isoformat()
    } for c in recent_comments]

    return Response({
        'success': True,
        'data': {
            'conversations': conversations_data,
            'bookings': bookings_data,
            'contacts': contacts_data,
            'comments': comments_data
        }
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get Analytics Data',
    description='Get analytics data for charts and graphs.',
    parameters=[
        OpenApiParameter(name='period', type=str, description="Period: 'week', 'month', 'year' (default: week)")
    ],
    responses={
        200: OpenApiResponse(description='Analytics data for charts')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_data(request):
    """Get analytics data for charts."""
    period = request.query_params.get('period', 'week')

    today = timezone.now().date()

    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 365

    # Generate date range
    date_labels = []
    conversation_counts = []
    booking_counts = []
    contact_counts = []

    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        date_labels.append(date.strftime('%Y-%m-%d'))

        conversation_counts.append(
            ConversationSession.objects.filter(created_at__date=date).count()
        )
        booking_counts.append(
            BookingSession.objects.filter(created_at__date=date).count()
        )
        contact_counts.append(
            ContactSubmission.objects.filter(created_at__date=date).count()
        )

    # Popular countries
    from django.db.models import Count
    popular_countries = StudentProfile.objects.values('preferred_country').annotate(
        count=Count('preferred_country')
    ).order_by('-count')[:5]

    # Booking status distribution
    booking_status = BookingSession.objects.values('status').annotate(
        count=Count('status')
    )

    return Response({
        'success': True,
        'data': {
            'timeline': {
                'labels': date_labels,
                'conversations': conversation_counts,
                'bookings': booking_counts,
                'contacts': contact_counts
            },
            'popular_countries': list(popular_countries),
            'booking_status': list(booking_status)
        }
    })


# ============================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin Users'],
    summary='List Admin Users',
    description='Get list of all admin users.',
    operation_id='admin_users_list_all',
    parameters=[
        OpenApiParameter(name='role', type=str, description="Filter by role: 'admin', 'superadmin'"),
        OpenApiParameter(name='search', type=str, description='Search by username or email')
    ],
    responses={
        200: OpenApiResponse(response=AdminUserListSerializer(many=True))
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    """List all admin users."""
    queryset = User.objects.filter(is_staff=True).order_by('-date_joined')

    # Filter by role
    role = request.query_params.get('role')
    if role == 'superadmin':
        queryset = queryset.filter(is_superuser=True)
    elif role == 'admin':
        queryset = queryset.filter(is_superuser=False)

    # Search
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    serializer = AdminUserListSerializer(queryset, many=True)

    return Response({
        'success': True,
        'count': queryset.count(),
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin Users'],
    summary='Get User Details',
    description='Get detailed information about a specific admin user.',
    operation_id='admin_users_get_by_id',
    responses={
        200: OpenApiResponse(response=AdminUserSerializer),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_user(request, user_id):
    """Get admin user details."""
    user = get_object_or_404(User, id=user_id, is_staff=True)
    serializer = AdminUserSerializer(user)

    return Response({
        'success': True,
        'data': serializer.data
    })


@extend_schema(
    tags=['Admin Users'],
    summary='Create Admin User',
    description='Create a new admin user. Requires superadmin privileges.',
    request=AdminUserCreateSerializer,
    responses={
        201: OpenApiResponse(response=AdminUserSerializer),
        400: OpenApiResponse(description='Validation error'),
        403: OpenApiResponse(description='Not a superadmin')
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_user(request):
    """Create a new admin user."""
    # Only superadmins can create users
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Only superadmins can create new admin users'
        }, status=status.HTTP_403_FORBIDDEN)

    serializer = AdminUserCreateSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'success': True,
            'message': 'Admin user created successfully',
            'data': AdminUserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Users'],
    summary='Update Admin User',
    description='Update an admin user. Requires superadmin privileges.',
    request=AdminUserUpdateSerializer,
    responses={
        200: OpenApiResponse(response=AdminUserSerializer),
        400: OpenApiResponse(description='Validation error'),
        403: OpenApiResponse(description='Not a superadmin'),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_user(request, user_id):
    """Update an admin user."""
    # Only superadmins can update other users
    if not request.user.is_superuser and request.user.id != user_id:
        return Response({
            'success': False,
            'error': 'Only superadmins can update other admin users'
        }, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User, id=user_id)
    serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'User updated successfully',
            'data': AdminUserSerializer(user).data
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Users'],
    summary='Delete Admin User',
    description='Delete an admin user. Requires superadmin privileges.',
    responses={
        200: OpenApiResponse(description='User deleted'),
        403: OpenApiResponse(description='Not a superadmin'),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    """Delete an admin user."""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Only superadmins can delete admin users'
        }, status=status.HTTP_403_FORBIDDEN)

    if request.user.id == user_id:
        return Response({
            'success': False,
            'error': 'Cannot delete yourself'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()

    return Response({
        'success': True,
        'message': f'User "{username}" deleted successfully'
    })


@extend_schema(
    tags=['Admin Users'],
    summary='Reset User Password',
    description='Reset another user\'s password. Requires superadmin privileges.',
    request=ResetPasswordSerializer,
    responses={
        200: OpenApiResponse(description='Password reset successfully'),
        403: OpenApiResponse(description='Not a superadmin'),
        404: OpenApiResponse(description='User not found')
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_user_password(request, user_id):
    """Reset another user's password."""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Only superadmins can reset passwords'
        }, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User, id=user_id)
    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({
            'success': True,
            'message': f'Password for "{user.username}" reset successfully'
        })

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# QUICK ACTIONS ENDPOINTS
# ============================================================

@extend_schema(
    tags=['Admin Quick Actions'],
    summary='Get Pending Items Count',
    description='Get count of items requiring attention.',
    responses={
        200: OpenApiResponse(
            description='Pending items counts',
            examples=[
                OpenApiExample(
                    'Counts',
                    value={
                        'success': True,
                        'data': {
                            'pending_bookings': 5,
                            'unread_contacts': 10,
                            'pending_comments': 3
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_items(request):
    """Get count of items requiring attention."""
    return Response({
        'success': True,
        'data': {
            'pending_bookings': BookingSession.objects.filter(status='pending').count(),
            'unread_contacts': ContactSubmission.objects.filter(read=False).count(),
            'pending_comments': BlogComment.objects.filter(status='pending').count()
        }
    })


@extend_schema(
    tags=['Admin Quick Actions'],
    summary='Search All',
    description='Search across all entities (students, bookings, contacts, posts).',
    parameters=[
        OpenApiParameter(name='q', type=str, description='Search query', required=True)
    ],
    responses={
        200: OpenApiResponse(description='Search results')
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def global_search(request):
    """Search across all entities."""
    query = request.query_params.get('q', '').strip()

    if not query or len(query) < 2:
        return Response({
            'success': False,
            'error': 'Search query must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Search students
    students = StudentProfile.objects.filter(
        Q(name__icontains=query) |
        Q(preferred_country__icontains=query)
    )[:5]

    # Search bookings
    bookings = BookingSession.objects.filter(
        Q(student_name__icontains=query) |
        Q(student_email__icontains=query)
    )[:5]

    # Search contacts
    contacts = ContactSubmission.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query)
    )[:5]

    # Search blog posts
    posts = BlogPost.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query),
        is_deleted=False
    )[:5]

    return Response({
        'success': True,
        'data': {
            'students': [{
                'id': s.id,
                'name': s.name,
                'country': s.preferred_country,
                'type': 'student'
            } for s in students],
            'bookings': [{
                'id': str(b.booking_id),
                'name': b.student_name,
                'status': b.status,
                'type': 'booking'
            } for b in bookings],
            'contacts': [{
                'id': str(c.id),
                'name': c.name,
                'email': c.email,
                'type': 'contact'
            } for c in contacts],
            'posts': [{
                'id': str(p.post_id),
                'title': p.title,
                'status': p.status,
                'type': 'post'
            } for p in posts]
        }
    })
