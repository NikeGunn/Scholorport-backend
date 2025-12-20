"""
API Views for Scholarport Backend.

This module provides all the REST API endpoints for the chatbot functionality,
including conversation management, institution recommendations, and admin features.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
import json
import uuid
from datetime import datetime

from .models import ConversationSession, ChatMessage, University, StudentProfile
from .services.conversation_manager import ConversationManager
from .services.university_selector import UniversitySelector
from .services.profile_creator import ProfileCreator


# Initialize our services
conversation_manager = ConversationManager()
university_selector = UniversitySelector()
profile_creator = ProfileCreator()


@extend_schema(
    tags=['Chat'],
    summary='Start a new conversation',
    description='''
    Initialize a new chatbot conversation session.

    This endpoint creates a new conversation session and returns a unique session_id
    that must be used for all subsequent messages in this conversation.

    The response includes the welcome message and the first question to ask the user.
    ''',
    request=None,
    responses={
        201: OpenApiResponse(
            description='Conversation started successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'current_step': 1,
                        'message': 'Welcome to Scholarport! I\'m here to help you find the perfect university.',
                        'question': 'What is your name?',
                        'total_steps': 7
                    }
                )
            ]
        ),
        500: OpenApiResponse(
            description='Server error',
            examples=[
                OpenApiExample(
                    'Error Response',
                    value={'success': False, 'error': 'Failed to start conversation: error details'}
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def start_conversation(request):
    """
    Start a new conversation session.

    Returns:
        - session_id: Unique identifier for this conversation
        - current_step: Current step in the conversation (1)
        - message: Welcome message
        - question: First question to ask
    """
    try:
        # Create new conversation session
        session = ConversationSession.objects.create(
            session_id=uuid.uuid4(),
            current_step=1,
            is_completed=False
        )

        # Get welcome message and first question
        welcome_data = conversation_manager.get_welcome_message()

        # Save welcome message to chat history
        ChatMessage.objects.create(
            conversation=session,
            sender='bot',
            message_text=welcome_data['message'],
            step_number=0
        )

        return Response({
            'success': True,
            'session_id': str(session.session_id),
            'current_step': session.current_step,
            'message': welcome_data['message'],
            'question': welcome_data['question'],
            'total_steps': 7
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to start conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Chat'],
    summary='Send a message in conversation',
    description='''
    Send a user message in an existing conversation session.

    This endpoint processes the user's response, advances the conversation,
    and returns the bot's response along with the next question if applicable.

    When the conversation is complete, university recommendations are included
    in the response.
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'format': 'uuid', 'description': 'The conversation session ID'},
                'message': {'type': 'string', 'description': 'User message/response'}
            },
            'required': ['session_id', 'message'],
            'example': {
                'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'message': 'John Doe'
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description='Message processed successfully',
            examples=[
                OpenApiExample(
                    'Conversation Continues',
                    value={
                        'success': True,
                        'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'current_step': 2,
                        'bot_response': 'Nice to meet you, John! Let me help you find the right university.',
                        'next_question': 'What is your education level?',
                        'completed': False,
                        'total_steps': 7
                    }
                ),
                OpenApiExample(
                    'Conversation Completed',
                    value={
                        'success': True,
                        'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'current_step': 7,
                        'bot_response': 'Based on your preferences, here are my recommendations...',
                        'completed': True,
                        'total_steps': 7,
                        'recommendations': [
                            {'name': 'Harvard University', 'country': 'USA', 'ranking': 1}
                        ],
                        'profile_created': True,
                        'profile_id': 123
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid request - missing fields or completed conversation'),
        404: OpenApiResponse(description='Session not found'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def send_message(request):
    """
    Send a message in an existing conversation.

    Expected payload:
        - session_id: The conversation session ID
        - message: User's message/response

    Returns:
        - success: Whether the message was processed
        - session_id: The session ID
        - current_step: Current step after processing
        - bot_response: Bot's response to user message
        - next_question: Next question (if conversation continues)
        - completed: Whether conversation is complete
        - recommendations: University recommendations (if completed)
    """
    try:
        # Get request data
        session_id = request.data.get('session_id')
        user_message = request.data.get('message', '').strip()

        if not session_id or not user_message:
            return Response({
                'success': False,
                'error': 'session_id and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get conversation session
        try:
            session = ConversationSession.objects.get(session_id=session_id)
        except ConversationSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid session_id'
            }, status=status.HTTP_404_NOT_FOUND)

        if session.is_completed:
            return Response({
                'success': False,
                'error': 'Conversation already completed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Save user message
        ChatMessage.objects.create(
            conversation=session,
            sender='user',
            message_text=user_message,
            step_number=session.current_step
        )

        # Process the message with our conversation manager
        response_data = conversation_manager.process_user_input(str(session.session_id), user_message)

        # Refresh session from database to get updated values
        session.refresh_from_db()

        # Save bot response
        ChatMessage.objects.create(
            conversation=session,
            sender='bot',
            message_text=response_data['bot_response'],
            step_number=session.current_step
        )

        # Prepare response
        api_response = {
            'success': True,
            'session_id': str(session.session_id),
            'current_step': session.current_step,
            'bot_response': response_data['bot_response'],
            'completed': session.is_completed,
            'total_steps': 7
        }

        # Add next question if conversation continues
        if not session.is_completed and response_data.get('next_question'):
            api_response['next_question'] = response_data['next_question']

        # If conversation is completed, get university recommendations
        if session.is_completed:
            recommendations = university_selector.select_universities(session)
            api_response['recommendations'] = recommendations

            # Create student profile
            profile = profile_creator.create_profile(session, recommendations)
            api_response['profile_created'] = True
            api_response['profile_id'] = profile.id

        return Response(api_response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to process message: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Chat'],
    summary='Get conversation history',
    description='''
    Retrieve the complete chat history for a conversation session.

    Returns all messages exchanged between the user and bot in chronological order.
    ''',
    operation_id='get_conversation_history',
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='The conversation session ID'
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Conversation history retrieved',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'messages': [
                            {'type': 'bot', 'content': 'Welcome!', 'step_number': 0, 'timestamp': '2024-01-01T10:00:00Z'},
                            {'type': 'user', 'content': 'John Doe', 'step_number': 1, 'timestamp': '2024-01-01T10:01:00Z'}
                        ],
                        'current_step': 2,
                        'completed': False,
                        'created_at': '2024-01-01T10:00:00Z'
                    }
                )
            ]
        ),
        404: OpenApiResponse(description='Session not found'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation_history(request, session_id):
    """
    Get the chat history for a conversation session.

    Returns:
        - session_id: The session ID
        - messages: List of all messages in conversation
        - current_step: Current step
        - completed: Whether conversation is complete
        - created_at: When conversation started
    """
    try:
        # Get conversation session
        session = get_object_or_404(ConversationSession, session_id=session_id)

        # Get all messages
        messages = ChatMessage.objects.filter(
            conversation=session
        ).order_by('timestamp')

        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'type': msg.sender,
                'content': msg.message_text,
                'step_number': msg.step_number,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
            })

        return Response({
            'success': True,
            'session_id': str(session.session_id),
            'messages': formatted_messages,
            'current_step': session.current_step,
            'completed': session.is_completed,
            'created_at': session.created_at.isoformat() if session.created_at else None
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get conversation history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Institutions'],
    summary='Get all institutions',
    description='''
    Retrieve a list of institutions (universities/colleges) with optional filtering.

    Supports filtering by country, tuition, ranking, and text search.
    Results are paginated with a default limit of 50.
    ''',
    operation_id='list_institutions',
    parameters=[
        OpenApiParameter(name='country', type=OpenApiTypes.STR, description='Filter by country name'),
        OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Search in institution name'),
        OpenApiParameter(name='max_tuition', type=OpenApiTypes.STR, description='Maximum tuition filter'),
        OpenApiParameter(name='min_ranking', type=OpenApiTypes.INT, description='Minimum ranking filter'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Number of results (default: 50)')
    ],
    responses={
        200: OpenApiResponse(
            description='Institutions retrieved successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'institutions': [
                            {
                                'id': 1,
                                'name': 'Harvard University',
                                'country': 'USA',
                                'city': 'Cambridge',
                                'tuition': '$50,000/year',
                                'programs': ['Computer Science', 'MBA'],
                                'ranking': 1,
                                'ielts_requirement': '7.0',
                                'toefl_requirement': '100',
                                'affordability': 'High',
                                'region': 'North America'
                            }
                        ],
                        'total_count': 1
                    }
                )
            ]
        ),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_institutions(request):
    """
    Get all institutions with optional filtering.

    Query Parameters:
        - country: Filter by country
        - max_tuition: Maximum tuition amount
        - min_ranking: Minimum ranking
        - search: Search in institution name
        - limit: Limit results (default 50)
    """
    try:
        institutions = University.objects.all()

        # Apply filters
        country = request.GET.get('country')
        if country:
            institutions = institutions.filter(country__icontains=country)

        search = request.GET.get('search')
        if search:
            institutions = institutions.filter(university_name__icontains=search)

        max_tuition = request.GET.get('max_tuition')
        if max_tuition:
            # This is simplified - in reality you'd need more complex tuition parsing
            institutions = institutions.filter(tuition__icontains=max_tuition)

        # Limit results
        limit = int(request.GET.get('limit', 50))
        institutions = institutions[:limit]

        # Format response
        institution_list = []
        for uni in institutions:
            institution_list.append({
                'id': uni.id,
                'name': uni.university_name,
                'country': uni.country,
                'city': uni.city,
                'tuition': uni.tuition,
                'programs': uni.programs[:5] if uni.programs else [],  # Limit programs
                'ranking': uni.ranking,
                'ielts_requirement': uni.ielts_requirement,
                'toefl_requirement': uni.toefl_requirement,
                'affordability': uni.affordability,
                'region': uni.region
            })

        return Response({
            'success': True,
            'institutions': institution_list,
            'total_count': len(institution_list)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get institutions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Institutions'],
    summary='Get institution details',
    description='Retrieve detailed information about a specific institution by ID.',
    operation_id='get_institution_details',
    parameters=[
        OpenApiParameter(
            name='institution_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='The institution ID'
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Institution details retrieved',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'institution': {
                            'id': 1,
                            'name': 'Harvard University',
                            'country': 'USA',
                            'city': 'Cambridge',
                            'tuition': '$50,000/year',
                            'programs': ['Computer Science', 'MBA', 'Law'],
                            'ranking': 1,
                            'ielts_requirement': '7.0',
                            'toefl_requirement': '100',
                            'affordability': 'High',
                            'region': 'North America',
                            'notes': 'Ivy League university'
                        }
                    }
                )
            ]
        ),
        404: OpenApiResponse(description='Institution not found'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_institution_details(request, institution_id=None, university_id=None):
    """
    Get detailed information about a specific institution.
    Supports both institution_id and university_id for backward compatibility.
    """
    try:
        # Support both new and old parameter names for backward compatibility
        lookup_id = institution_id or university_id
        institution = get_object_or_404(University, id=lookup_id)

        return Response({
            'success': True,
            'institution': {
                'id': institution.id,
                'name': institution.university_name,
                'country': institution.country,
                'city': institution.city,
                'tuition': institution.tuition,
                'programs': institution.programs,
                'ranking': institution.ranking,
                'ielts_requirement': institution.ielts_requirement,
                'toefl_requirement': institution.toefl_requirement,
                'affordability': institution.affordability,
                'region': institution.region,
                'notes': institution.notes
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get institution details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Panel API Views (for counselors)

@extend_schema(
    tags=['Admin'],
    summary='Get dashboard statistics',
    description='''
    Retrieve dashboard statistics for the admin panel.

    Returns metrics including total conversations, completion rates,
    popular destination countries, and recent activity.
    ''',
    responses={
        200: OpenApiResponse(
            description='Dashboard stats retrieved',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'stats': {
                            'total_conversations': 150,
                            'completed_conversations': 120,
                            'total_profiles': 100,
                            'completion_rate': 80.0,
                            'popular_countries': ['USA', 'UK', 'Canada', 'Australia', 'Germany'],
                            'recent_activity': 25,
                            'profile_stats': {}
                        }
                    }
                )
            ]
        ),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Add admin authentication
def admin_dashboard_stats(request):
    """
    Get dashboard statistics for admin panel.

    Returns:
        - total_conversations: Total number of conversations
        - completed_conversations: Number of completed conversations
        - total_profiles: Number of student profiles created
        - popular_countries: Most popular destination countries
        - recent_activity: Recent conversation activity
    """
    try:
        # Get basic stats
        total_conversations = ConversationSession.objects.count()
        completed_conversations = ConversationSession.objects.filter(is_completed=True).count()
        total_profiles = StudentProfile.objects.count()

        # Get popular countries
        from django.db.models import Count
        popular_countries = StudentProfile.objects.values('preferred_country').annotate(
            count=Count('preferred_country')
        ).order_by('-count')[:5]

        # Get recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_conversations = ConversationSession.objects.filter(
            created_at__gte=yesterday
        ).count()

        # Get profile stats
        profile_stats = profile_creator.get_profile_stats()

        return Response({
            'success': True,
            'stats': {
                'total_conversations': total_conversations,
                'completed_conversations': completed_conversations,
                'total_profiles': total_profiles,
                'completion_rate': round((completed_conversations / total_conversations * 100), 2) if total_conversations > 0 else 0,
                'popular_countries': [item['preferred_country'] for item in popular_countries],
                'recent_activity': recent_conversations,
                'profile_stats': profile_stats
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get dashboard stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Admin'],
    summary='Get student profiles',
    description='''
    Retrieve all student profiles for the admin dashboard.

    Supports filtering by country and completion status, with pagination.
    ''',
    parameters=[
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Number of profiles (default: 50)'),
        OpenApiParameter(name='offset', type=OpenApiTypes.INT, description='Pagination offset (default: 0)'),
        OpenApiParameter(name='country', type=OpenApiTypes.STR, description='Filter by preferred country'),
        OpenApiParameter(name='completed_only', type=OpenApiTypes.BOOL, description='Show only completed conversations')
    ],
    responses={
        200: OpenApiResponse(
            description='Student profiles retrieved',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'profiles': [
                            {
                                'id': 1,
                                'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                                'student_name': 'John Doe',
                                'education_background': 'Bachelor\'s',
                                'budget': 'USD 50,000',
                                'test_score': 'IELTS 7.5',
                                'preferred_country': 'USA',
                                'recommended_universities': ['Harvard', 'MIT'],
                                'ai_insights': 'Strong candidate for top universities',
                                'created_at': '2024-01-01T10:00:00Z',
                                'conversation_completed': True
                            }
                        ],
                        'pagination': {
                            'total_count': 100,
                            'limit': 50,
                            'offset': 0,
                            'has_more': True
                        }
                    }
                )
            ]
        ),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Add admin authentication
def admin_get_student_profiles(request):
    """
    Get all student profiles for admin dashboard.

    Query Parameters:
        - limit: Number of profiles to return (default 50)
        - offset: Offset for pagination
        - country: Filter by preferred country
        - completed_only: Show only completed conversations
    """
    try:
        profiles = StudentProfile.objects.select_related('conversation').all()

        # Apply filters
        completed_only = request.GET.get('completed_only', 'false').lower() == 'true'
        if completed_only:
            profiles = profiles.filter(conversation__is_completed=True)

        country = request.GET.get('country')
        if country:
            profiles = profiles.filter(preferred_country__icontains=country)

        # Pagination
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        total_count = profiles.count()
        profiles = profiles[offset:offset + limit]

        # Format profiles
        profile_list = []
        for profile in profiles:
            universities = profile.recommended_universities or []
            uni_names = [uni.get('name', '') for uni in universities]

            profile_list.append({
                'id': profile.id,
                'session_id': str(profile.conversation.session_id),
                'student_name': profile.name,
                'education_background': profile.education_level,
                'budget': f"{profile.budget_currency} {profile.budget_amount:,}",
                'test_score': f"{profile.test_type} {profile.test_score}",
                'preferred_country': profile.preferred_country,
                'recommended_universities': uni_names,
                'ai_insights': getattr(profile, 'ai_insights', 'AI insights not available'),
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'conversation_completed': profile.conversation.is_completed
            })

        return Response({
            'success': True,
            'profiles': profile_list,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get student profiles: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Admin'],
    summary='Export data to Excel',
    description='''
    Export all completed student profiles to an Excel file.

    Returns an Excel file (.xlsx) download containing all student data
    including conversation details and university recommendations.
    ''',
    responses={
        200: OpenApiResponse(
            description='Excel file download',
            response={'type': 'string', 'format': 'binary'}
        ),
        404: OpenApiResponse(description='No completed profiles to export'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Add admin authentication
def admin_export_excel(request):
    """
    Export all completed student profiles to Excel file
    Handles both browser and JavaScript requests
    """
    try:
        from django.http import HttpResponse
        import io
        import pandas as pd
        from datetime import datetime

        # Get all completed profiles
        profiles = StudentProfile.objects.select_related('conversation').filter(
            conversation__is_completed=True
        ).order_by('-created_at')

        if not profiles.exists():
            return Response({
                'success': False,
                'error': 'No completed profiles to export'
            }, status=404)

        # Prepare data for Excel
        data = []
        for profile in profiles:
            conversation = profile.conversation
            messages = conversation.messages.all().order_by('timestamp')

            # Extract conversation data using step numbers instead of flawed counting
            student_responses = {}
            for msg in messages:
                if msg.sender == 'user':
                    # Use step_number to properly map responses
                    if msg.step_number == 1:
                        student_responses['name'] = msg.message_text
                    elif msg.step_number == 2:
                        student_responses['education'] = msg.message_text
                    elif msg.step_number == 3:
                        student_responses['test_score'] = msg.message_text
                    elif msg.step_number == 4:
                        student_responses['budget'] = msg.message_text
                    elif msg.step_number == 5:
                        student_responses['country'] = msg.message_text

            # Parse recommended universities (assuming it's stored as a string or list)
            recommended_unis = profile.recommended_universities
            if isinstance(recommended_unis, str):
                try:
                    import json
                    recommended_unis = json.loads(recommended_unis)
                except:
                    recommended_unis = [recommended_unis] if recommended_unis else []
            elif not isinstance(recommended_unis, list):
                recommended_unis = []

            # Prepare row data
            row = {
                'Session ID': conversation.session_id,
                'Student Name': student_responses.get('name', profile.name or 'Unknown'),
                'Education Background': student_responses.get('education', profile.education_level or 'Not provided'),
                'Test Score': student_responses.get('test_score', f"{profile.test_type or 'Unknown'}: {profile.test_score or 'N/A'}"),
                'Budget': student_responses.get('budget', f"{profile.budget_amount or 'Unknown'} {profile.budget_currency or ''}").strip(),
                'Preferred Country': student_responses.get('country', profile.preferred_country or 'Not specified'),
                'University 1': recommended_unis[0] if len(recommended_unis) > 0 else '',
                'University 2': recommended_unis[1] if len(recommended_unis) > 1 else '',
                'University 3': recommended_unis[2] if len(recommended_unis) > 2 else '',
                'Conversation Completed': 'Yes' if conversation.is_completed else 'No',
                'Created Date': profile.created_at.strftime('%Y-%m-%d %H:%M:%S') if profile.created_at else 'Unknown',
            }
            data.append(row)

        # Create DataFrame and Excel file
        df = pd.DataFrame(data)

        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Student Profiles', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Student Profiles']
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)

        excel_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Scholarport_Student_Data_{timestamp}.xlsx'

        # Create HTTP response with proper headers
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(excel_buffer.getvalue())

        # Add CORS headers for JavaScript requests
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition, Content-Length'

        return response

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to export Excel: {str(e)}'
        }, status=500)


@extend_schema(
    tags=['Admin'],
    summary='Export Firebase data',
    description='''
    Export data directly from Firebase Firestore.

    Supports JSON and Excel export formats.
    ''',
    parameters=[
        OpenApiParameter(
            name='format',
            type=OpenApiTypes.STR,
            description='Export format: json or excel (default: json)',
            enum=['json', 'excel']
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Data export (JSON or Excel file)',
            response={'type': 'string', 'format': 'binary'}
        ),
        400: OpenApiResponse(description='Invalid format specified'),
        404: OpenApiResponse(description='No data found in Firebase'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Add admin authentication
def admin_export_firebase_data(request):
    """
    Export data directly from Firebase Firestore
    Returns JSON or Excel format
    """
    try:
        from django.conf import settings
        import firebase_admin
        from firebase_admin import firestore
        import json
        from datetime import datetime
        import logging

        # Suppress Google Cloud ALTS warnings
        logging.getLogger('google.auth.transport.grpc').setLevel(logging.ERROR)
        logging.getLogger('google.auth._default').setLevel(logging.ERROR)

        # Get format parameter (json or excel)
        export_format = request.GET.get('format', 'json').lower()

        # Initialize Firestore client
        db = firestore.client()

        # Get all student profiles from Firebase
        profiles_ref = db.collection('student_profiles')
        profiles = profiles_ref.stream()

        # Collect all data
        firebase_data = []
        for profile in profiles:
            profile_data = profile.to_dict()
            profile_data['firebase_id'] = profile.id
            firebase_data.append(profile_data)

        if not firebase_data:
            return Response({
                'success': False,
                'error': 'No data found in Firebase'
            }, status=404)

        # Return JSON format
        if export_format == 'json':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'firebase_data_{timestamp}.json'

            response = HttpResponse(
                json.dumps(firebase_data, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        # Return Excel format
        elif export_format == 'excel':
            import pandas as pd
            import io

            # Flatten the nested data for Excel
            flattened_data = []
            for item in firebase_data:
                flat_item = {
                    'Firebase ID': item.get('firebase_id', ''),
                    'Session ID': item.get('session_id', ''),
                    'Student Name': item.get('student_info', {}).get('name', ''),
                    'Education': item.get('student_info', {}).get('education_level', ''),
                    'Budget Amount': item.get('student_info', {}).get('budget', {}).get('amount', ''),
                    'Budget Currency': item.get('student_info', {}).get('budget', {}).get('currency', ''),
                    'Test Type': item.get('student_info', {}).get('test_score', {}).get('type', ''),
                    'Test Score': item.get('student_info', {}).get('test_score', {}).get('score', ''),
                    'Preferred Country': item.get('student_info', {}).get('preferred_country', ''),
                    'Universities': ', '.join([uni.get('name', '') for uni in item.get('recommendations', {}).get('universities', [])]),
                    'Created Date': item.get('metadata', {}).get('created_at', ''),
                    'Name Response': item.get('conversation_data', {}).get('name_response', ''),
                    'Education Response': item.get('conversation_data', {}).get('education_response', ''),
                    'Test Score Response': item.get('conversation_data', {}).get('test_score_response', ''),
                    'Budget Response': item.get('conversation_data', {}).get('budget_response', ''),
                    'Country Response': item.get('conversation_data', {}).get('country_response', '')
                }
                flattened_data.append(flat_item)

            # Create DataFrame
            df = pd.DataFrame(flattened_data)

            # Create Excel file
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Firebase Data', index=False)

                # Auto-adjust column widths
                worksheet = writer.sheets['Firebase Data']
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value)) for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)

            excel_buffer.seek(0)

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'Firebase_Student_Data_{timestamp}.xlsx'

            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(excel_buffer.getvalue())

            return response

        else:
            return Response({
                'success': False,
                'error': 'Invalid format. Use ?format=json or ?format=excel'
            }, status=400)

    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to export Firebase data: {str(e)}'
        }, status=500)


@extend_schema(
    tags=['Chat'],
    summary='Handle data consent',
    description='''
    Handle user consent for data saving.

    Called when users respond to the data saving question
    after receiving university recommendations.
    ''',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'format': 'uuid', 'description': 'The conversation session ID'},
                'consent': {'type': 'boolean', 'description': 'Whether user consents to data saving'}
            },
            'required': ['session_id', 'consent'],
            'example': {
                'session_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'consent': True
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description='Consent handled successfully',
            examples=[
                OpenApiExample(
                    'Consent Given',
                    value={'success': True, 'message': 'Your data has been saved successfully.'}
                ),
                OpenApiExample(
                    'Consent Declined',
                    value={'success': True, 'message': 'Your data will not be saved. Thank you for using Scholarport!'}
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid request'),
        500: OpenApiResponse(description='Server error')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def handle_data_consent(request):
    """
    Handle user consent for data saving.

    This endpoint is called when users respond to the data saving question
    after getting their university recommendations.

    Expected payload:
    {
        "session_id": "uuid-string",
        "consent": true/false
    }

    Returns:
        Response message based on consent choice
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        consent = data.get('consent')

        if not session_id or consent is None:
            return Response({
                'success': False,
                'error': 'session_id and consent are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Handle the consent response
        result = conversation_manager.handle_data_consent(session_id, consent)

        return Response(result, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Health'],
    summary='Health check',
    description='Simple health check endpoint to verify the API is running.',
    responses={
        200: OpenApiResponse(
            description='API is healthy',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'message': 'Scholarport Backend API is running',
                        'timestamp': '2024-01-01T10:00:00.000000',
                        'version': '1.0.0'
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint to verify API is working.
    """
    return Response({
        'success': True,
        'message': 'Scholarport Backend API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)
