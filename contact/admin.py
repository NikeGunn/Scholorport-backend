"""
Contact App Admin Configuration
"""
from django.contrib import admin
from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'type', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['name', 'email', 'message']
    list_editable = ['read']
    ordering = ['-created_at']
    readonly_fields = ['id', 'name', 'email', 'phone', 'message', 'type', 'ip_address', 'user_agent', 'created_at', 'updated_at']

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'type')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Admin', {
            'fields': ('read', 'notes')
        }),
        ('Metadata', {
            'fields': ('id', 'ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Disable adding submissions from admin - they come from frontend."""
        return False
