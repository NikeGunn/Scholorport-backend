"""
Partners App Admin Configuration
"""
from django.contrib import admin
from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'country', 'featured', 'is_active', 'order', 'created_at']
    list_filter = ['type', 'featured', 'is_active', 'country']
    search_fields = ['name', 'description', 'country']
    list_editable = ['featured', 'is_active', 'order']
    ordering = ['order', '-featured', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'country')
        }),
        ('Visual', {
            'fields': ('logo',)
        }),
        ('Details', {
            'fields': ('description', 'website')
        }),
        ('Status', {
            'fields': ('featured', 'is_active', 'order')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
