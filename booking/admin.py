"""
Booking App Admin Configuration

Rich admin interface for managing counselor bookings.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import (
    CounselorProfile,
    CounselorAvailability,
    BookingSession,
    BookingReminder
)


class CounselorAvailabilityInline(admin.TabularInline):
    """Inline admin for counselor availability."""
    model = CounselorAvailability
    extra = 1
    fields = ['weekday', 'start_time', 'end_time', 'specific_date', 'is_available']


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
    """Admin interface for counselor availability."""
    list_display = ['counselor', 'get_weekday', 'start_time', 'end_time', 'specific_date', 'is_available']
    list_filter = ['counselor', 'weekday', 'is_available']
    search_fields = ['counselor__user__first_name', 'counselor__user__last_name']

    def get_weekday(self, obj):
        return obj.get_weekday_display()
    get_weekday.short_description = 'Weekday'
    get_weekday.admin_order_field = 'weekday'


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
