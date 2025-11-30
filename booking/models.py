"""
Booking App Models

This module contains models for counselor session booking functionality.
Students can book consultation sessions with counselors.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class CounselorProfile(models.Model):
    """
    Extended profile for counselors (staff users who provide consultations).
    Links to Django's built-in User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='counselor_profile'
    )

    # Professional Information
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Senior Education Consultant"
    )
    bio = models.TextField(
        blank=True,
        help_text="Professional biography and experience"
    )
    specializations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of specialization areas, e.g., ['UK Universities', 'STEM Programs']"
    )
    years_of_experience = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )

    # Contact and Availability
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(
        upload_to='counselors/profiles/',
        blank=True,
        null=True
    )

    # Meeting Configuration
    meeting_duration_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        help_text="Default session duration in minutes"
    )
    meeting_link = models.URLField(
        blank=True,
        help_text="Default video meeting link (Zoom, Google Meet, etc.)"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether counselor is accepting new bookings"
    )
    max_daily_sessions = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'counselor_profiles'
        verbose_name = 'Counselor Profile'
        verbose_name_plural = 'Counselor Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.title}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email


class CounselorAvailability(models.Model):
    """
    Defines available time slots for counselors.
    Can be recurring weekly or specific dates.
    """
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    counselor = models.ForeignKey(
        CounselorProfile,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )

    # Time slot definition
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        help_text="Day of the week (for recurring availability)"
    )
    start_time = models.TimeField(help_text="Start time of availability window")
    end_time = models.TimeField(help_text="End time of availability window")

    # Optional: Specific date override (for one-time availability/unavailability)
    specific_date = models.DateField(
        null=True,
        blank=True,
        help_text="If set, this availability applies only to this specific date"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="False = blocked/unavailable during this time"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'counselor_availabilities'
        verbose_name = 'Counselor Availability'
        verbose_name_plural = 'Counselor Availabilities'
        ordering = ['weekday', 'start_time']
        unique_together = [
            ['counselor', 'weekday', 'start_time', 'end_time', 'specific_date']
        ]

    def __str__(self):
        if self.specific_date:
            return f"{self.counselor.full_name} - {self.specific_date} {self.start_time}-{self.end_time}"
        return f"{self.counselor.full_name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class BookingSession(models.Model):
    """
    Represents a booked consultation session between a student and counselor.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    SESSION_TYPE_CHOICES = [
        ('initial', 'Initial Consultation'),
        ('followup', 'Follow-up Session'),
        ('document_review', 'Document Review'),
        ('application_help', 'Application Assistance'),
        ('visa_guidance', 'Visa Guidance'),
        ('general', 'General Inquiry'),
    ]

    # Unique identifier
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Public booking reference ID"
    )

    # Relationships
    counselor = models.ForeignKey(
        CounselorProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bookings'
    )

    # Link to existing conversation (optional)
    conversation = models.ForeignKey(
        'chat.ConversationSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        help_text="Link to chat conversation if booking originated from chat"
    )

    # Student Information (no auth required)
    student_name = models.CharField(max_length=255)
    student_email = models.EmailField()
    student_phone = models.CharField(max_length=20, blank=True)

    # Session Details
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default='initial'
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)

    # Meeting Details
    meeting_link = models.URLField(
        blank=True,
        help_text="Video call link for the session"
    )
    meeting_notes = models.TextField(
        blank=True,
        help_text="Pre-session notes or agenda from student"
    )

    # Status Management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Verification (email-based, no login required)
    verification_token = models.UUIDField(
        default=uuid.uuid4,
        help_text="Token for email verification and booking management"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether student email has been verified"
    )

    # Post-Session
    counselor_notes = models.TextField(
        blank=True,
        help_text="Notes from counselor after session"
    )
    student_feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Cancellation details
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.CharField(
        max_length=20,
        blank=True,
        choices=[('student', 'Student'), ('counselor', 'Counselor'), ('system', 'System')]
    )

    class Meta:
        db_table = 'booking_sessions'
        verbose_name = 'Booking Session'
        verbose_name_plural = 'Booking Sessions'
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['booking_id']),
            models.Index(fields=['student_email']),
            models.Index(fields=['status', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.student_name} with {self.counselor}"

    @property
    def is_upcoming(self):
        from django.utils import timezone
        from datetime import datetime
        session_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return session_datetime > timezone.now().replace(tzinfo=None)

    @property
    def can_cancel(self):
        """Check if booking can still be cancelled (24 hours before)"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        session_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return session_datetime > (timezone.now().replace(tzinfo=None) + timedelta(hours=24))


class BookingReminder(models.Model):
    """
    Tracks reminders sent for bookings.
    """
    REMINDER_TYPE_CHOICES = [
        ('confirmation', 'Booking Confirmation'),
        ('reminder_24h', '24 Hour Reminder'),
        ('reminder_1h', '1 Hour Reminder'),
        ('followup', 'Post-Session Follow-up'),
    ]

    booking = models.ForeignKey(
        BookingSession,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to = models.EmailField()
    was_successful = models.BooleanField(default=True)

    class Meta:
        db_table = 'booking_reminders'
        verbose_name = 'Booking Reminder'
        verbose_name_plural = 'Booking Reminders'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.booking.booking_id} - {self.reminder_type}"
