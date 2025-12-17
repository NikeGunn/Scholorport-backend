"""
Booking App Admin Configuration

Rich admin interface for managing counselor bookings.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from django import forms
from .models import (
    CounselorProfile,
    CounselorAvailability,
    BookingSession,
    BookingReminder
)


def generate_time_choices():
    """Generate time choices for every 15 minutes from 00:00 to 23:45."""
    choices = []
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            time_str = f'{hour:02d}:{minute:02d}'
            display_str = f'{hour:02d}:{minute:02d}'
            # Add AM/PM for easier reading
            if hour == 0:
                display_str = f'12:{minute:02d} AM (Midnight)'
            elif hour < 12:
                display_str = f'{hour}:{minute:02d} AM'
            elif hour == 12:
                display_str = f'12:{minute:02d} PM (Noon)'
            else:
                display_str = f'{hour-12}:{minute:02d} PM'
            choices.append((time_str, display_str))
    return choices


TIME_CHOICES = generate_time_choices()


class CounselorAvailabilityForm(forms.ModelForm):
    """Custom form with user-friendly time selection."""
    start_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        help_text="Select the start time for this availability slot",
        widget=forms.Select(attrs={'style': 'width: 200px;'})
    )
    end_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        help_text="Select the end time for this availability slot",
        widget=forms.Select(attrs={'style': 'width: 200px;'})
    )

    class Meta:
        model = CounselorAvailability
        fields = '__all__'

    def clean_start_time(self):
        """Convert string back to time object."""
        from datetime import datetime
        time_str = self.cleaned_data['start_time']
        return datetime.strptime(time_str, '%H:%M').time()

    def clean_end_time(self):
        """Convert string back to time object."""
        from datetime import datetime
        time_str = self.cleaned_data['end_time']
        return datetime.strptime(time_str, '%H:%M').time()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data


class CounselorAvailabilityInlineForm(forms.ModelForm):
    """Custom form for inline availability with user-friendly time selection."""
    start_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'style': 'width: 150px;'})
    )
    end_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'style': 'width: 150px;'})
    )

    class Meta:
        model = CounselorAvailability
        fields = ['weekday', 'start_time', 'end_time', 'specific_date', 'is_available']

    def clean_start_time(self):
        from datetime import datetime
        time_str = self.cleaned_data['start_time']
        return datetime.strptime(time_str, '%H:%M').time()

    def clean_end_time(self):
        from datetime import datetime
        time_str = self.cleaned_data['end_time']
        return datetime.strptime(time_str, '%H:%M').time()


class CounselorAvailabilityInline(admin.TabularInline):
    """Inline admin for counselor availability with user-friendly time selection."""
    model = CounselorAvailability
    form = CounselorAvailabilityInlineForm
    extra = 1
    fields = ['weekday', 'start_time', 'end_time', 'specific_date', 'is_available']
    verbose_name = "Availability Slot"
    verbose_name_plural = "📅 Availability Slots (Add counselor's available time slots)"


class BookingReminderInline(admin.TabularInline):
    """Inline admin for booking reminders."""
    model = BookingReminder
    extra = 0
    readonly_fields = ['reminder_type', 'sent_at', 'sent_to', 'was_successful']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CounselorProfile)
class CounselorProfileAdmin(admin.ModelAdmin):
    """Admin interface for counselor profiles."""
    list_display = [
        'get_counselor_name', 'title', 'email', 'phone',
        'get_specializations', 'is_active', 'get_booking_count', 'created_at'
    ]
    list_filter = ['is_active', 'years_of_experience', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CounselorAvailabilityInline]

    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('title', 'bio', 'specializations', 'years_of_experience')
        }),
        ('Contact', {
            'fields': ('phone', 'profile_image')
        }),
        ('Meeting Settings', {
            'fields': ('meeting_duration_minutes', 'meeting_link', 'max_daily_sessions')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_counselor_name(self, obj):
        return obj.full_name
    get_counselor_name.short_description = 'Name'
    get_counselor_name.admin_order_field = 'user__first_name'

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'

    def get_specializations(self, obj):
        if obj.specializations:
            return ', '.join(obj.specializations[:3])
        return '-'
    get_specializations.short_description = 'Specializations'

    def get_booking_count(self, obj):
        count = obj.bookings.filter(status__in=['confirmed', 'completed']).count()
        return format_html('<span style="font-weight:bold;">{}</span>', count)
    get_booking_count.short_description = 'Bookings'


@admin.register(CounselorAvailability)
class CounselorAvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for counselor availability with user-friendly time selection."""
    form = CounselorAvailabilityForm
    list_display = ['counselor', 'get_weekday', 'get_time_slot', 'specific_date', 'availability_status']
    list_filter = ['counselor', 'weekday', 'is_available']
    search_fields = ['counselor__user__first_name', 'counselor__user__last_name']
    list_editable = ['specific_date']
    ordering = ['counselor', 'weekday', 'start_time']

    fieldsets = (
        ('Counselor', {
            'fields': ('counselor',),
            'description': 'Select the counselor for this availability slot.'
        }),
        ('Schedule', {
            'fields': ('weekday', 'start_time', 'end_time'),
            'description': '📅 Set the day and time range for this availability slot. '
                          'The counselor will be available for bookings during this time.'
        }),
        ('Special Settings', {
            'fields': ('specific_date', 'is_available'),
            'description': '⚙️ Optional: Set a specific date for one-time availability, '
                          'or mark as unavailable to block a time slot.',
            'classes': ('collapse',)
        }),
    )

    def get_weekday(self, obj):
        return obj.get_weekday_display()
    get_weekday.short_description = 'Day'
    get_weekday.admin_order_field = 'weekday'

    def get_time_slot(self, obj):
        """Display time slot in a user-friendly format."""
        start = obj.start_time.strftime('%I:%M %p').lstrip('0')
        end = obj.end_time.strftime('%I:%M %p').lstrip('0')
        return format_html(
            '<span style="font-weight: bold; color: #2c3e50;">{} - {}</span>',
            start, end
        )
    get_time_slot.short_description = 'Time Slot'
    get_time_slot.admin_order_field = 'start_time'

    def availability_status(self, obj):
        """Display availability status with icon."""
        if obj.is_available:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✅ Available</span>'
            )
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">❌ Blocked</span>'
        )
    availability_status.short_description = 'Status'


class BookingStatusFilter(admin.SimpleListFilter):
    """Custom filter for booking status with counts."""
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class UpcomingBookingsFilter(admin.SimpleListFilter):
    """Filter for upcoming vs past bookings."""
    title = 'Timeline'
    parameter_name = 'timeline'

    def lookups(self, request, model_admin):
        return [
            ('upcoming', 'Upcoming'),
            ('today', 'Today'),
            ('past', 'Past'),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'upcoming':
            return queryset.filter(scheduled_date__gt=today)
        elif self.value() == 'today':
            return queryset.filter(scheduled_date=today)
        elif self.value() == 'past':
            return queryset.filter(scheduled_date__lt=today)
        return queryset


@admin.register(BookingSession)
class BookingSessionAdmin(admin.ModelAdmin):
    """Admin interface for booking sessions."""
    list_display = [
        'get_booking_id_short', 'student_name', 'student_email',
        'get_counselor', 'get_session_type', 'get_scheduled_datetime',
        'get_status_badge', 'is_verified', 'created_at'
    ]
    list_filter = [
        BookingStatusFilter, UpcomingBookingsFilter, 'session_type',
        'is_verified', 'counselor', 'created_at'
    ]
    search_fields = [
        'booking_id', 'student_name', 'student_email', 'student_phone',
        'counselor__user__first_name', 'counselor__user__last_name'
    ]
    readonly_fields = [
        'booking_id', 'verification_token', 'created_at', 'updated_at',
        'confirmed_at', 'completed_at', 'cancelled_at'
    ]
    inlines = [BookingReminderInline]
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date', '-scheduled_time']

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'status', 'session_type')
        }),
        ('Student Information', {
            'fields': ('student_name', 'student_email', 'student_phone')
        }),
        ('Session Details', {
            'fields': (
                'counselor', 'scheduled_date', 'scheduled_time',
                'duration_minutes', 'meeting_link', 'meeting_notes'
            )
        }),
        ('Verification', {
            'fields': ('verification_token', 'is_verified'),
            'classes': ('collapse',)
        }),
        ('Related', {
            'fields': ('conversation',),
            'classes': ('collapse',)
        }),
        ('Post-Session', {
            'fields': ('counselor_notes', 'student_feedback', 'rating'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_confirmed', 'mark_completed', 'mark_no_show', 'export_to_excel']

    def get_booking_id_short(self, obj):
        return str(obj.booking_id)[:8]
    get_booking_id_short.short_description = 'Booking ID'

    def get_counselor(self, obj):
        if obj.counselor:
            return obj.counselor.full_name
        return '-'
    get_counselor.short_description = 'Counselor'
    get_counselor.admin_order_field = 'counselor__user__first_name'

    def get_session_type(self, obj):
        return obj.get_session_type_display()
    get_session_type.short_description = 'Type'

    def get_scheduled_datetime(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.scheduled_date.strftime('%Y-%m-%d'),
            obj.scheduled_time.strftime('%H:%M')
        )
    get_scheduled_datetime.short_description = 'Scheduled'

    def get_status_badge(self, obj):
        colors = {
            'pending': '#f39c12',
            'confirmed': '#3498db',
            'completed': '#27ae60',
            'cancelled': '#e74c3c',
            'no_show': '#95a5a6',
            'rescheduled': '#9b59b6',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'

    @admin.action(description='Mark selected as Confirmed')
    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='confirmed',
            confirmed_at=timezone.now()
        )
        self.message_user(request, f'{updated} booking(s) marked as confirmed.')

    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status='confirmed').update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} booking(s) marked as completed.')

    @admin.action(description='Mark selected as No Show')
    def mark_no_show(self, request, queryset):
        updated = queryset.filter(status='confirmed').update(status='no_show')
        self.message_user(request, f'{updated} booking(s) marked as no show.')

    @admin.action(description='Export to Excel')
    def export_to_excel(self, request, queryset):
        import io
        from django.http import HttpResponse

        try:
            import pandas as pd
        except ImportError:
            self.message_user(request, 'pandas is required for Excel export', level='error')
            return

        data = []
        for booking in queryset:
            data.append({
                'Booking ID': str(booking.booking_id),
                'Student Name': booking.student_name,
                'Student Email': booking.student_email,
                'Student Phone': booking.student_phone,
                'Counselor': booking.counselor.full_name if booking.counselor else '',
                'Session Type': booking.get_session_type_display(),
                'Date': booking.scheduled_date.strftime('%Y-%m-%d'),
                'Time': booking.scheduled_time.strftime('%H:%M'),
                'Status': booking.get_status_display(),
                'Created': booking.created_at.strftime('%Y-%m-%d %H:%M'),
            })

        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="bookings_export.xlsx"'
        return response


@admin.register(BookingReminder)
class BookingReminderAdmin(admin.ModelAdmin):
    """Admin interface for booking reminders."""
    list_display = ['booking', 'reminder_type', 'sent_to', 'sent_at', 'was_successful']
    list_filter = ['reminder_type', 'was_successful', 'sent_at']
    search_fields = ['booking__booking_id', 'sent_to']
    readonly_fields = ['booking', 'reminder_type', 'sent_at', 'sent_to', 'was_successful']

    def has_add_permission(self, request):
        return False
