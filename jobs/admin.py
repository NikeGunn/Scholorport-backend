"""
Jobs/Careers App Admin Configuration

Admin interface for managing job postings.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for job postings."""

    list_display = [
        'title',
        'slug',
        'department',
        'location',
        'type',
        'is_active_display',
        'is_featured_display',
        'is_expired_display',
        'posted_at',
        'expires_at',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'is_featured',
        'type',
        'department',
        'created_at',
        'expires_at'
    ]

    search_fields = [
        'title',
        'slug',
        'department',
        'location',
        'description',
        'requirements',
        'responsibilities'
    ]

    prepopulated_fields = {'slug': ('title',)}

    readonly_fields = ['id', 'created_at', 'updated_at']

    ordering = ['-created_at']

    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'department', 'location', 'type')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'responsibilities'),
            'classes': ('wide',)
        }),
        ('Application', {
            'fields': ('application_email', 'application_method')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Dates', {
            'fields': ('posted_at', 'expires_at')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']

    def is_active_display(self, obj):
        """Display active status with icon."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = 'Status'
    is_active_display.admin_order_field = 'is_active'

    def is_featured_display(self, obj):
        """Display featured status with icon."""
        if obj.is_featured:
            return format_html('<span style="color: gold;">★ Featured</span>')
        return format_html('<span style="color: gray;">☆</span>')
    is_featured_display.short_description = 'Featured'
    is_featured_display.admin_order_field = 'is_featured'

    def is_expired_display(self, obj):
        """Display expired status."""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        if obj.expires_at:
            days_left = (obj.expires_at - timezone.now()).days
            if days_left <= 7:
                return format_html(f'<span style="color: orange;">{days_left}d left</span>')
            return format_html(f'<span style="color: green;">{days_left}d left</span>')
        return format_html('<span style="color: gray;">No expiry</span>')
    is_expired_display.short_description = 'Expiry'

    @admin.action(description='Mark selected jobs as active')
    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} job(s) marked as active.')

    @admin.action(description='Mark selected jobs as inactive')
    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} job(s) marked as inactive.')

    @admin.action(description='Mark selected jobs as featured')
    def make_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} job(s) marked as featured.')

    @admin.action(description='Remove featured status')
    def remove_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} job(s) removed from featured.')
