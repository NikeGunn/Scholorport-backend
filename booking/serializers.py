"""
Booking App Serializers

Serializers for counselor booking API endpoints.
"""
from typing import Optional
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import (
    CounselorProfile,
    CounselorAvailability,
    BookingSession,
    BookingReminder
)


class BookingUserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization in booking module."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']

    @extend_schema_field(OpenApiTypes.STR)
    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username


class CounselorAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for counselor availability slots."""
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = CounselorAvailability
        fields = [
            'id', 'weekday', 'weekday_display', 'start_time', 'end_time',
            'specific_date', 'is_available', 'created_at'
        ]
        read_only_fields = ['created_at']


class CounselorProfileListSerializer(serializers.ModelSerializer):
    """Serializer for listing counselors (minimal info)."""
    full_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = CounselorProfile
        fields = [
            'id', 'full_name', 'email', 'title', 'specializations',
            'years_of_experience', 'profile_image_url', 'is_active',
            'meeting_duration_minutes'
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_profile_image_url(self, obj) -> Optional[str]:
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


class CounselorProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed counselor profile."""
    user = BookingUserBasicSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    availabilities = CounselorAvailabilitySerializer(many=True, read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    total_bookings = serializers.SerializerMethodField()

    class Meta:
        model = CounselorProfile
        fields = [
            'id', 'user', 'full_name', 'email', 'title', 'bio',
            'specializations', 'years_of_experience', 'phone',
            'profile_image', 'profile_image_url', 'meeting_duration_minutes',
            'meeting_link', 'is_active', 'max_daily_sessions',
            'availabilities', 'total_bookings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.URI)
    def get_profile_image_url(self, obj) -> Optional[str]:
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_total_bookings(self, obj) -> int:
        return obj.bookings.filter(status__in=['confirmed', 'completed']).count()


class CounselorProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating counselor profiles (admin use)."""

    class Meta:
        model = CounselorProfile
        fields = [
            'user', 'title', 'bio', 'specializations', 'years_of_experience',
            'phone', 'profile_image', 'meeting_duration_minutes',
            'meeting_link', 'is_active', 'max_daily_sessions'
        ]


class BookingSessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings."""
    counselor_name = serializers.CharField(source='counselor.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = BookingSession
        fields = [
            'id', 'booking_id', 'counselor_name', 'student_name', 'student_email',
            'session_type', 'session_type_display', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'status', 'status_display', 'is_upcoming',
            'is_verified', 'created_at'
        ]


class BookingSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed booking view."""
    counselor = CounselorProfileListSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    session_type_display = serializers.CharField(source='get_session_type_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    # Include verification_token for testing (in production, this would only be sent via email)
    verification_token = serializers.UUIDField(read_only=True)

    class Meta:
        model = BookingSession
        fields = [
            'id', 'booking_id', 'verification_token', 'counselor', 'conversation',
            'student_name', 'student_email', 'student_phone',
            'session_type', 'session_type_display', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'meeting_link', 'meeting_notes',
            'status', 'status_display', 'is_verified', 'is_upcoming', 'can_cancel',
            'counselor_notes', 'student_feedback', 'rating',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at',
            'cancelled_at', 'cancellation_reason', 'cancelled_by'
        ]
        read_only_fields = [
            'booking_id', 'verification_token', 'is_verified',
            'confirmed_at', 'completed_at', 'cancelled_at'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new booking."""
    counselor_id = serializers.IntegerField(write_only=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = BookingSession
        fields = [
            'counselor_id', 'conversation_id',
            'student_name', 'student_email', 'student_phone',
            'session_type', 'scheduled_date', 'scheduled_time',
            'meeting_notes'
        ]

    def validate_counselor_id(self, value):
        try:
            counselor = CounselorProfile.objects.get(id=value, is_active=True)
        except CounselorProfile.DoesNotExist:
            raise serializers.ValidationError("Counselor not found or not available.")
        return value

    def validate_scheduled_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot book a session in the past.")
        if value > timezone.now().date() + timedelta(days=90):
            raise serializers.ValidationError("Cannot book more than 90 days in advance.")
        return value

    def validate(self, data):
        counselor = CounselorProfile.objects.get(id=data['counselor_id'])
        scheduled_datetime = datetime.combine(data['scheduled_date'], data['scheduled_time'])

        # Check if slot is available
        existing = BookingSession.objects.filter(
            counselor=counselor,
            scheduled_date=data['scheduled_date'],
            scheduled_time=data['scheduled_time'],
            status__in=['pending', 'confirmed']
        ).exists()

        if existing:
            raise serializers.ValidationError({
                'scheduled_time': "This time slot is already booked."
            })

        return data

    def create(self, validated_data):
        counselor_id = validated_data.pop('counselor_id')
        conversation_id = validated_data.pop('conversation_id', None)

        counselor = CounselorProfile.objects.get(id=counselor_id)
        validated_data['counselor'] = counselor
        validated_data['duration_minutes'] = counselor.meeting_duration_minutes
        validated_data['meeting_link'] = counselor.meeting_link

        if conversation_id:
            from chat.models import ConversationSession
            try:
                validated_data['conversation'] = ConversationSession.objects.get(
                    session_id=conversation_id
                )
            except ConversationSession.DoesNotExist:
                pass

        return super().create(validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating booking details."""

    class Meta:
        model = BookingSession
        fields = [
            'scheduled_date', 'scheduled_time', 'session_type',
            'meeting_notes', 'student_phone'
        ]

    def validate_scheduled_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot reschedule to a past date.")
        return value


class BookingCancelSerializer(serializers.Serializer):
    """Serializer for cancelling a booking."""
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        booking = self.context.get('booking')
        if booking and not booking.can_cancel:
            raise serializers.ValidationError(
                "Cannot cancel within 24 hours of the scheduled time."
            )
        return data


class BookingVerifySerializer(serializers.Serializer):
    """Serializer for verifying booking via token."""
    verification_token = serializers.UUIDField()


class BookingFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for submitting post-session feedback."""

    class Meta:
        model = BookingSession
        fields = ['student_feedback', 'rating']

    def validate_rating(self, value):
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots."""
    date = serializers.DateField()
    time = serializers.TimeField()
    counselor_id = serializers.IntegerField()
    counselor_name = serializers.CharField()
    duration_minutes = serializers.IntegerField()


class BookingReminderSerializer(serializers.ModelSerializer):
    """Serializer for booking reminders."""
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)

    class Meta:
        model = BookingReminder
        fields = [
            'id', 'reminder_type', 'reminder_type_display',
            'sent_at', 'sent_to', 'was_successful'
        ]
