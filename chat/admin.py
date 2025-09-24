"""
Django Admin Configuration for Scholarport Backend

This module provides a comprehensive admin interface for managing:
- Student Conversations and Messages
- University Data
- Student Profiles
- Data Export and Analytics

Features:
- Advanced filtering and search
- Bulk operations and exports
- Custom admin actions
- Rich data visualization
- Excel/JSON export functionality
"""

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils.safestring import mark_safe
import json
import pandas as pd
import io
from datetime import datetime, timedelta

from .models import ConversationSession, ChatMessage, University, StudentProfile


# Custom Admin Filters
class ContactInfoFilter(admin.SimpleListFilter):
    """Filter conversations by contact information completeness"""
    title = 'Contact Information'
    parameter_name = 'contact_info'

    def lookups(self, request, model_admin):
        return (
            ('complete', 'Has Email & Phone'),
            ('partial', 'Missing Email or Phone'),
            ('none', 'No Contact Info'),
            ('email_only', 'Has Email Only'),
            ('phone_only', 'Has Phone Only'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'complete':
            return queryset.exclude(
                Q(student_email__isnull=True) | Q(student_email__exact='') |
                Q(student_phone__isnull=True) | Q(student_phone__exact='')
            )
        elif self.value() == 'partial':
            return queryset.filter(
                (Q(student_email__isnull=True) | Q(student_email__exact='')) |
                (Q(student_phone__isnull=True) | Q(student_phone__exact=''))
            ).exclude(
                (Q(student_email__isnull=True) | Q(student_email__exact='')) &
                (Q(student_phone__isnull=True) | Q(student_phone__exact=''))
            )
        elif self.value() == 'none':
            return queryset.filter(
                (Q(student_email__isnull=True) | Q(student_email__exact='')) &
                (Q(student_phone__isnull=True) | Q(student_phone__exact=''))
            )
        elif self.value() == 'email_only':
            return queryset.exclude(
                Q(student_email__isnull=True) | Q(student_email__exact='')
            ).filter(
                Q(student_phone__isnull=True) | Q(student_phone__exact='')
            )
        elif self.value() == 'phone_only':
            return queryset.exclude(
                Q(student_phone__isnull=True) | Q(student_phone__exact='')
            ).filter(
                Q(student_email__isnull=True) | Q(student_email__exact='')
            )


# Unregister Group model (we don't need it for this app)
admin.site.unregister(Group)


class ChatMessageInline(admin.TabularInline):
    """Inline display for chat messages within conversation admin"""
    model = ChatMessage
    extra = 0
    readonly_fields = ('timestamp', 'sender', 'step_number')
    fields = ('step_number', 'sender', 'message_text', 'timestamp')

    def has_add_permission(self, request, obj=None):
        return False  # Don't allow adding messages through admin


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    """
    Advanced admin interface for managing conversation sessions.

    Features:
    - Rich list display with status indicators
    - Advanced filtering by completion, dates, countries
    - Search across student names and responses
    - Inline message display
    - Custom admin actions for bulk operations
    """

    list_display = (
        'session_id_short',
        'student_name_display',
        'contact_info_display',
        'completion_status',
        'current_step_display',
        'country_flag',
        'test_score_badge',
        'university_count',
        'created_date',
        'consent_status'
    )

    list_filter = (
        'is_completed',
        'current_step',
        'data_save_consent',
        'counselor_contacted',
        'created_at',
        'processed_country',
        ContactInfoFilter,
        ('student_email', admin.EmptyFieldListFilter),
        ('student_phone', admin.EmptyFieldListFilter),
        ('email_response', admin.EmptyFieldListFilter),
        ('phone_response', admin.EmptyFieldListFilter),
    )

    search_fields = (
        'session_id',
        'processed_name',
        'name_response',
        'processed_education',
        'processed_country',
        'student_email',
        'processed_email',
        'email_response',
        'student_phone',
        'processed_phone',
        'phone_response'
    )

    readonly_fields = (
        'session_id',
        'created_at',
        'updated_at',
        'completed_at',
        'conversation_summary',
        'contact_info_display'
    )

    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'current_step', 'is_completed', 'completed_at')
        }),
        ('Student Information', {
            'fields': ('student_name', 'student_email', 'student_phone')
        }),
        ('Raw Responses', {
            'fields': ('name_response', 'education_response', 'test_score_response',
                      'budget_response', 'country_response', 'email_response', 'phone_response'),
            'classes': ('collapse',)
        }),
        ('Processed Responses', {
            'fields': ('processed_name', 'processed_education', 'processed_test_score',
                      'processed_budget', 'processed_country', 'processed_email', 'processed_phone')
        }),
        ('University Recommendations', {
            'fields': ('suggested_universities',),
            'classes': ('collapse',)
        }),
        ('Data Management', {
            'fields': ('data_save_consent', 'counselor_contacted')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('conversation_summary', 'contact_info_display')
        })
    )

    inlines = [ChatMessageInline]

    actions = [
        'export_to_excel',
        'export_to_json',
        'mark_counselor_contacted',
        'generate_university_report',
        'identify_missing_contacts',
        'send_contact_request'
    ]

    change_list_template = 'admin/conversation_changelist.html'

    def get_urls(self):
        """Add custom URLs for data export"""
        urls = super().get_urls()
        custom_urls = [
            path('export-all-data/', self.admin_site.admin_view(self.export_all_data), name='chat_export_all_data'),
            path('download-complete-database/', self.admin_site.admin_view(self.download_complete_database), name='chat_download_database'),
        ]
        return custom_urls + urls

    def session_id_short(self, obj):
        """Display shortened session ID with copy button"""
        short_id = str(obj.session_id)[:8]
        return format_html(
            '<span title="{}" style="font-family: monospace;">{}</span>',
            obj.session_id, short_id
        )
    session_id_short.short_description = 'Session ID'

    def student_name_display(self, obj):
        """Display student name with profile link if exists"""
        name = obj.processed_name or obj.name_response or 'Anonymous'
        try:
            profile = obj.student_profile
            profile_url = reverse('admin:chat_studentprofile_change', args=[profile.id])
            return format_html(
                '<a href="{}" title="View Profile"><strong>{}</strong></a>',
                profile_url, name
            )
        except:
            return name
    student_name_display.short_description = 'Student Name'

    def contact_info_display(self, obj):
        """Display contact information with status indicators"""
        email = obj.processed_email or obj.email_response or obj.student_email
        phone = obj.processed_phone or obj.phone_response or obj.student_phone

        contact_html = '<div style="font-size: 12px;">'

        if email:
            contact_html += f'<div style="color: #28a745;">📧 {email[:25]}{"..." if len(email) > 25 else ""}</div>'
        else:
            contact_html += '<div style="color: #dc3545;">📧 No email</div>'

        if phone:
            contact_html += f'<div style="color: #28a745;">📞 {phone}</div>'
        else:
            contact_html += '<div style="color: #dc3545;">📞 No phone</div>'

        contact_html += '</div>'
        return format_html(contact_html)
    contact_info_display.short_description = 'Contact Info'

    def completion_status(self, obj):
        """Visual completion status indicator"""
        if obj.is_completed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Completed</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">⏳ In Progress</span>'
            )
    completion_status.short_description = 'Status'

    def current_step_display(self, obj):
        """Display current step with progress bar"""
        steps = ['Name', 'Education', 'Test Score', 'Budget', 'Country', 'Complete']
        step_name = steps[min(obj.current_step - 1, len(steps) - 1)] if obj.current_step <= len(steps) else 'Complete'
        progress = min((obj.current_step / 6) * 100, 100)

        return format_html(
            '<div title="Step {}/6: {}"><div style="background: #ddd; width: 60px; height: 8px; border-radius: 4px;"><div style="background: #007cba; width: {}%; height: 100%; border-radius: 4px;"></div></div><small>{}</small></div>',
            obj.current_step, step_name, progress, step_name
        )
    current_step_display.short_description = 'Progress'

    def country_flag(self, obj):
        """Display country with flag emoji"""
        country = obj.processed_country or obj.country_response
        if not country:
            return '-'

        # Simple country flag mapping
        flags = {
            'usa': '🇺🇸', 'united states': '🇺🇸', 'america': '🇺🇸',
            'canada': '🇨🇦', 'uk': '🇬🇧', 'united kingdom': '🇬🇧', 'britain': '🇬🇧',
            'australia': '🇦🇺', 'germany': '🇩🇪', 'france': '🇫🇷', 'europe': '🇪🇺',
            'netherlands': '🇳🇱', 'sweden': '🇸🇪', 'norway': '🇳🇴', 'denmark': '🇩🇰'
        }

        flag = flags.get(country.lower(), '🌍')
        return format_html('{} {}', flag, country)
    country_flag.short_description = 'Country'

    def test_score_badge(self, obj):
        """Display test score with color coding"""
        score = obj.processed_test_score or obj.test_score_response
        if not score:
            return '-'

        # Extract score for color coding
        try:
            if 'IELTS' in score.upper():
                score_num = float(score.split()[-1])
                if score_num >= 7.0:
                    color = '#28a745'  # Green
                elif score_num >= 6.0:
                    color = '#ffc107'  # Yellow
                else:
                    color = '#dc3545'  # Red
            else:
                color = '#007bff'  # Blue for TOEFL or others
        except:
            color = '#6c757d'  # Gray for unparseable

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, score
        )
    test_score_badge.short_description = 'Test Score'

    def university_count(self, obj):
        """Display count of recommended universities"""
        count = len(obj.suggested_universities) if obj.suggested_universities else 0
        if count > 0:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">{}</span>',
                count
            )
        return '0'
    university_count.short_description = 'Universities'

    def created_date(self, obj):
        """Friendly date display"""
        return obj.created_at.strftime('%m/%d/%Y %H:%M')
    created_date.short_description = 'Created'

    def consent_status(self, obj):
        """Data consent status indicator"""
        if obj.data_save_consent:
            return format_html('<span style="color: green;">✓ Consented</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗ No Consent</span>')
    consent_status.short_description = 'Data Consent'

    def conversation_summary(self, obj):
        """Rich conversation summary"""
        if not obj.is_completed:
            return "Conversation not completed yet"

        summary = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h4 style="color: #495057; margin-top: 0;">Conversation Summary</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px; font-weight: bold; width: 120px;">Student:</td><td style="padding: 5px;">{obj.processed_name or 'Not provided'}</td></tr>
                <tr><td style="padding: 5px; font-weight: bold;">Education:</td><td style="padding: 5px;">{obj.processed_education or 'Not provided'}</td></tr>
                <tr><td style="padding: 5px; font-weight: bold;">Test Score:</td><td style="padding: 5px;">{obj.processed_test_score or 'Not provided'}</td></tr>
                <tr><td style="padding: 5px; font-weight: bold;">Budget:</td><td style="padding: 5px;">{obj.processed_budget or 'Not provided'}</td></tr>
                <tr><td style="padding: 5px; font-weight: bold;">Country:</td><td style="padding: 5px;">{obj.processed_country or 'Not provided'}</td></tr>
                <tr><td style="padding: 5px; font-weight: bold;">Universities:</td><td style="padding: 5px;">{len(obj.suggested_universities)} recommended</td></tr>
            </table>
        </div>
        """
        return format_html(summary)
    conversation_summary.short_description = 'Summary'

    # Custom Admin Actions
    def export_to_excel(self, request, queryset):
        """Export selected conversations to Excel"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="conversations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        data = []
        for conv in queryset:
            data.append({
                'Session ID': str(conv.session_id),
                'Student Name': conv.processed_name or conv.name_response or 'Anonymous',
                'Email': conv.student_email or 'Not provided',
                'Education': conv.processed_education or conv.education_response or 'Not provided',
                'Test Score': conv.processed_test_score or conv.test_score_response or 'Not provided',
                'Budget': conv.processed_budget or conv.budget_response or 'Not provided',
                'Country': conv.processed_country or conv.country_response or 'Not provided',
                'Status': 'Completed' if conv.is_completed else 'In Progress',
                'Universities': len(conv.suggested_universities) if conv.suggested_universities else 0,
                'Data Consent': 'Yes' if conv.data_save_consent else 'No',
                'Created Date': conv.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Conversations', index=False)
        excel_buffer.seek(0)
        response.write(excel_buffer.getvalue())

        self.message_user(request, f"Successfully exported {len(data)} conversations to Excel.")
        return response

    export_to_excel.short_description = "📊 Export selected to Excel"

    def export_to_json(self, request, queryset):
        """Export selected conversations to JSON"""
        data = []
        for conv in queryset:
            data.append(conv.get_conversation_data())

        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="conversations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'

        self.message_user(request, f"Successfully exported {len(data)} conversations to JSON.")
        return response

    export_to_json.short_description = "📄 Export selected to JSON"

    def mark_counselor_contacted(self, request, queryset):
        """Mark selected conversations as counselor contacted"""
        updated = queryset.update(counselor_contacted=True)
        self.message_user(request, f"Successfully marked {updated} conversations as counselor contacted.")

    mark_counselor_contacted.short_description = "📞 Mark as counselor contacted"

    def generate_university_report(self, request, queryset):
        """Generate university recommendation report"""
        university_stats = {}
        for conv in queryset:
            if conv.suggested_universities:
                for uni in conv.suggested_universities:
                    name = uni.get('name', 'Unknown')
                    if name not in university_stats:
                        university_stats[name] = 0
                    university_stats[name] += 1

        # Sort by popularity
        sorted_unis = sorted(university_stats.items(), key=lambda x: x[1], reverse=True)

        report = "University Recommendation Report\\n" + "="*50 + "\\n"
        for uni, count in sorted_unis[:10]:
            report += f"{uni}: {count} recommendations\\n"

        self.message_user(request, f"Report generated for {len(queryset)} conversations. Top university: {sorted_unis[0][0] if sorted_unis else 'None'} ({sorted_unis[0][1] if sorted_unis else 0} recommendations)")

    generate_university_report.short_description = "📈 Generate university report"

    def export_all_data(self, request):
        """Export all database data to Excel with multiple sheets"""
        try:
            from django.http import HttpResponse
            import pandas as pd
            import io
            from datetime import datetime

            # Create Excel writer object
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:

                # Export ConversationSessions
                sessions_data = []
                for session in ConversationSession.objects.all():
                    sessions_data.append({
                        'Session ID': str(session.session_id),
                        'Student Name': session.processed_name or session.name_response or 'Unknown',
                        'Email': session.processed_email or session.email_response or session.student_email or 'Not provided',
                        'Phone': session.processed_phone or session.phone_response or session.student_phone or 'Not provided',
                        'Current Step': session.current_step,
                        'Is Completed': 'Yes' if session.is_completed else 'No',
                        'Education': session.processed_education or session.education_response or 'Not provided',
                        'Test Score': session.processed_test_score or session.test_score_response or 'Not provided',
                        'Budget': session.processed_budget or session.budget_response or 'Not provided',
                        'Country': session.processed_country or session.country_response or 'Not provided',
                        'Data Consent': 'Yes' if session.data_save_consent else 'No',
                        'Counselor Contacted': 'Yes' if session.counselor_contacted else 'No',
                        'Created': session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'Unknown',
                        'Completed': session.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session.completed_at else 'Not completed'
                    })

                df_sessions = pd.DataFrame(sessions_data)
                df_sessions.to_excel(writer, sheet_name='Conversation Sessions', index=False)

                # Export ChatMessages
                messages_data = []
                for message in ChatMessage.objects.select_related('conversation'):
                    messages_data.append({
                        'Session ID': str(message.conversation.session_id),
                        'Step Number': message.step_number,
                        'Sender': message.sender,
                        'Message': message.message_text[:500] + '...' if len(message.message_text) > 500 else message.message_text,
                        'Timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    })

                df_messages = pd.DataFrame(messages_data)
                df_messages.to_excel(writer, sheet_name='Chat Messages', index=False)

                # Export Universities
                universities_data = []
                for uni in University.objects.all():
                    universities_data.append({
                        'Name': uni.university_name,
                        'Country': uni.country,
                        'City': uni.city or 'Not specified',
                        'Region': uni.region or 'Not specified',
                        'Ranking': uni.ranking or 'Unranked',
                        'Tuition': uni.tuition or 'Not specified',
                        'IELTS Requirement': uni.ielts_requirement or 'Not specified',
                        'TOEFL Requirement': uni.toefl_requirement or 'Not specified',
                        'Programs': len(uni.programs) if uni.programs else 0,
                        'Affordability': uni.affordability or 'Not specified',
                        'Notes': uni.notes or 'No notes'
                    })

                df_universities = pd.DataFrame(universities_data)
                df_universities.to_excel(writer, sheet_name='Universities', index=False)

                # Export StudentProfiles
                profiles_data = []
                for profile in StudentProfile.objects.select_related('conversation'):
                    profiles_data.append({
                        'Name': profile.name,
                        'Email': profile.email or 'Not provided',
                        'Phone': profile.phone or 'Not provided',
                        'Session ID': str(profile.conversation.session_id) if profile.conversation else 'No session',
                        'Education Level': profile.education_level,
                        'Field of Study': profile.field_of_study or 'Not specified',
                        'GPA': profile.gpa_percentage or 'Not provided',
                        'Test Type': profile.test_type,
                        'Test Score': profile.test_score,
                        'Budget Amount': profile.budget_amount,
                        'Budget Currency': profile.budget_currency,
                        'Preferred Country': profile.preferred_country,
                        'University Matches': len(profile.recommended_universities) if profile.recommended_universities else 0,
                        'Counselor': profile.assigned_counselor.username if profile.assigned_counselor else 'Unassigned',
                        'Contact Status': profile.contact_status,
                        'Created': profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Notes': profile.counselor_notes or 'No notes'
                    })

                df_profiles = pd.DataFrame(profiles_data)
                df_profiles.to_excel(writer, sheet_name='Student Profiles', index=False)

            excel_buffer.seek(0)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'Scholarport_Complete_Database_{timestamp}.xlsx'

            # Create HTTP response
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(excel_buffer.getvalue())

            return response

        except Exception as e:
            messages.error(request, f"Failed to export data: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    def download_complete_database(self, request):
        """Simplified database download method"""
        return self.export_all_data(request)

    def identify_missing_contacts(self, request, queryset):
        """Identify conversations with missing contact information"""
        missing_email = 0
        missing_phone = 0
        missing_both = 0

        for conversation in queryset:
            email = conversation.processed_email or conversation.email_response or conversation.student_email
            phone = conversation.processed_phone or conversation.phone_response or conversation.student_phone

            if not email and not phone:
                missing_both += 1
            elif not email:
                missing_email += 1
            elif not phone:
                missing_phone += 1

        self.message_user(
            request,
            f"Contact Analysis: {missing_both} missing both email & phone, {missing_email} missing email, {missing_phone} missing phone. "
            f"Total conversations needing follow-up: {missing_both + missing_email + missing_phone}/{len(queryset)}"
        )

    identify_missing_contacts.short_description = "🔍 Analyze missing contact info"

    def send_contact_request(self, request, queryset):
        """Mark conversations as needing contact information follow-up"""
        needs_followup = 0

        for conversation in queryset:
            email = conversation.processed_email or conversation.email_response or conversation.student_email
            phone = conversation.processed_phone or conversation.phone_response or conversation.student_phone

            if not email or not phone:
                # In a real implementation, this would send an email or SMS
                # For now, we'll just mark for manual follow-up
                needs_followup += 1

        self.message_user(
            request,
            f"Marked {needs_followup} conversations for contact follow-up. "
            f"Admin should manually reach out to collect missing email/phone information."
        )

    send_contact_request.short_description = "📞 Request missing contact details"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for chat messages with conversation context.

    Features:
    - Message flow visualization
    - Filtering by sender and conversation steps
    - Search across message content
    - Bulk operations for message management
    """

    list_display = (
        'conversation_short',
        'step_display',
        'sender_badge',
        'message_preview',
        'timestamp_display'
    )

    list_filter = (
        'sender',
        'step_number',
        'timestamp'
    )

    search_fields = (
        'message_text',
        'conversation__session_id',
        'conversation__processed_name'
    )

    readonly_fields = ('timestamp', 'conversation', 'sender')

    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'sender', 'step_number', 'timestamp')
        }),
        ('Content', {
            'fields': ('message_text',)
        }),
        ('AI Processing', {
            'fields': ('original_input', 'processed_output'),
            'classes': ('collapse',)
        })
    )

    actions = ['export_conversation_flow']

    def conversation_short(self, obj):
        """Display shortened conversation ID with link"""
        short_id = str(obj.conversation.session_id)[:8]
        conv_url = reverse('admin:chat_conversationsession_change', args=[obj.conversation.id])
        name = obj.conversation.processed_name or 'Anonymous'
        return format_html(
            '<a href="{}" title="View Conversation">{}<br><small>{}</small></a>',
            conv_url, short_id, name
        )
    conversation_short.short_description = 'Conversation'

    def step_display(self, obj):
        """Display step with icon"""
        step_icons = {
            0: '👋', 1: '📝', 2: '🎓', 3: '📊', 4: '💰', 5: '🌍'
        }
        step_names = {
            0: 'Welcome', 1: 'Name', 2: 'Education', 3: 'Test Score', 4: 'Budget', 5: 'Country'
        }
        icon = step_icons.get(obj.step_number, '💬')
        name = step_names.get(obj.step_number, f'Step {obj.step_number}')
        return format_html('{} {}', icon, name)
    step_display.short_description = 'Step'

    def sender_badge(self, obj):
        """Display sender with colored badge"""
        if obj.sender == 'bot':
            return format_html(
                '<span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">🤖 Bot</span>'
            )
        else:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">👤 User</span>'
            )
    sender_badge.short_description = 'Sender'

    def message_preview(self, obj):
        """Display message preview with length indicator"""
        preview = obj.message_text[:100]
        if len(obj.message_text) > 100:
            preview += '...'
        length = len(obj.message_text)
        return format_html(
            '<div title="Full length: {} characters">{}</div>',
            length, preview
        )
    message_preview.short_description = 'Message Preview'

    def timestamp_display(self, obj):
        """Friendly timestamp display"""
        return obj.timestamp.strftime('%m/%d %H:%M')
    timestamp_display.short_description = 'Time'

    def export_conversation_flow(self, request, queryset):
        """Export conversation flows to Excel"""
        conversations = {}
        for msg in queryset:
            conv_id = str(msg.conversation.session_id)
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append({
                'Step': msg.step_number,
                'Sender': msg.sender,
                'Message': msg.message_text,
                'Timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="conversation_flows_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            for conv_id, messages in conversations.items():
                df = pd.DataFrame(messages)
                sheet_name = f"Conv_{conv_id[:8]}"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        excel_buffer.seek(0)
        response.write(excel_buffer.getvalue())

        self.message_user(request, f"Successfully exported {len(conversations)} conversation flows.")
        return response

    export_conversation_flow.short_description = "💬 Export conversation flows"


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """
    Admin interface for university management with rich features.

    Features:
    - Country and program filtering
    - Tuition and requirement analysis
    - Bulk import/export capabilities
    - University matching tools
    """

    list_display = (
        'university_name',
        'country_flag',
        'city',
        'tuition_badge',
        'requirements_display',
        'ranking_badge',
        'program_count',
        'affordability_badge'
    )

    list_filter = (
        'country',
        'affordability',
        'region',
        'ranking'
    )

    search_fields = (
        'university_name',
        'country',
        'city',
        'programs',
        'searchable_text'
    )

    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('university_name', 'country', 'city', 'ranking')
        }),
        ('Financial Info', {
            'fields': ('tuition', 'affordability')
        }),
        ('Requirements', {
            'fields': ('ielts_requirement', 'toefl_requirement')
        }),
        ('Programs & Categories', {
            'fields': ('programs', 'program_categories')
        }),
        ('Additional Info', {
            'fields': ('region', 'notes', 'name_variations', 'searchable_text'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    actions = [
        'export_universities',
        'update_searchable_text',
        'analyze_requirements'
    ]

    def country_flag(self, obj):
        """Display country with flag"""
        flags = {
            'United States': '🇺🇸', 'Canada': '🇨🇦', 'United Kingdom': '🇬🇧',
            'Australia': '🇦🇺', 'Germany': '🇩🇪', 'France': '🇫🇷',
            'Netherlands': '🇳🇱', 'Sweden': '🇸🇪', 'Norway': '🇳🇴'
        }
        flag = flags.get(obj.country, '🌍')
        return format_html('{} {}', flag, obj.country)
    country_flag.short_description = 'Country'

    def tuition_badge(self, obj):
        """Display tuition with color coding"""
        if not obj.tuition:
            return '-'

        # Extract numeric value for color coding
        try:
            import re
            amount_match = re.search(r'(\d+(?:,\d+)*)', obj.tuition)
            if amount_match:
                amount = int(amount_match.group(1).replace(',', ''))
                if amount < 10000:
                    color = '#28a745'  # Green - affordable
                elif amount < 25000:
                    color = '#ffc107'  # Yellow - moderate
                else:
                    color = '#dc3545'  # Red - expensive
            else:
                color = '#6c757d'  # Gray
        except:
            color = '#6c757d'

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.tuition
        )
    tuition_badge.short_description = 'Tuition'

    def requirements_display(self, obj):
        """Display test requirements"""
        reqs = []
        if obj.ielts_requirement:
            reqs.append(f'IELTS {obj.ielts_requirement}')
        if obj.toefl_requirement:
            reqs.append(f'TOEFL {obj.toefl_requirement}')

        if reqs:
            return format_html(
                '<small>{}</small>',
                '<br>'.join(reqs)
            )
        return '-'
    requirements_display.short_description = 'Requirements'

    def ranking_badge(self, obj):
        """Display ranking with appropriate styling"""
        if not obj.ranking or obj.ranking == 'Community College':
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
                obj.ranking or 'Unranked'
            )

        try:
            rank_num = int(obj.ranking)
            if rank_num <= 100:
                color = '#28a745'  # Green - top tier
            elif rank_num <= 300:
                color = '#ffc107'  # Yellow - good
            else:
                color = '#007bff'  # Blue - standard
        except:
            color = '#6c757d'

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">#{}</span>',
            color, obj.ranking
        )
    ranking_badge.short_description = 'Ranking'

    def program_count(self, obj):
        """Display number of programs offered"""
        count = len(obj.programs) if obj.programs else 0
        return format_html(
            '<span title="{} programs">{}</span>',
            ', '.join(obj.programs) if obj.programs else 'No programs listed',
            count
        )
    program_count.short_description = 'Programs'

    def affordability_badge(self, obj):
        """Display affordability level"""
        colors = {
            'Very Affordable': '#28a745',
            'Affordable': '#20c997',
            'Moderate': '#ffc107',
            'Expensive': '#fd7e14',
            'Very Expensive': '#dc3545'
        }
        color = colors.get(obj.affordability, '#6c757d')

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.affordability or 'Unknown'
        )
    affordability_badge.short_description = 'Affordability'

    def export_universities(self, request, queryset):
        """Export universities to Excel"""
        data = []
        for uni in queryset:
            data.append({
                'University Name': uni.university_name,
                'Country': uni.country,
                'City': uni.city,
                'Tuition': uni.tuition,
                'IELTS Requirement': uni.ielts_requirement,
                'TOEFL Requirement': uni.toefl_requirement,
                'Ranking': uni.ranking,
                'Programs': ', '.join(uni.programs) if uni.programs else '',
                'Affordability': uni.affordability,
                'Region': uni.region,
                'Notes': uni.notes
            })

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="universities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Universities', index=False)
        excel_buffer.seek(0)
        response.write(excel_buffer.getvalue())

        self.message_user(request, f"Successfully exported {len(data)} universities.")
        return response

    export_universities.short_description = "🏫 Export universities to Excel"

    def update_searchable_text(self, request, queryset):
        """Update searchable text for selected universities"""
        updated = 0
        for uni in queryset:
            searchable = f"{uni.university_name} {uni.country} {uni.city} {' '.join(uni.programs or [])} {uni.notes or ''}"
            uni.searchable_text = searchable.lower()
            uni.save()
            updated += 1

        self.message_user(request, f"Updated searchable text for {updated} universities.")

    update_searchable_text.short_description = "🔍 Update searchable text"

    def analyze_requirements(self, request, queryset):
        """Analyze admission requirements"""
        ielts_scores = [uni.ielts_requirement for uni in queryset if uni.ielts_requirement]
        toefl_scores = [uni.toefl_requirement for uni in queryset if uni.toefl_requirement]

        avg_ielts = sum(ielts_scores) / len(ielts_scores) if ielts_scores else 0
        avg_toefl = sum(toefl_scores) / len(toefl_scores) if toefl_scores else 0

        self.message_user(
            request,
            f"Requirements Analysis: Avg IELTS {avg_ielts:.1f} ({len(ielts_scores)} unis), Avg TOEFL {avg_toefl:.0f} ({len(toefl_scores)} unis)"
        )

    analyze_requirements.short_description = "📊 Analyze requirements"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """
    Advanced admin interface for student profile management.

    Features:
    - Counselor assignment and tracking
    - Application status management
    - University recommendation analysis
    - Communication tracking
    - Advanced reporting and exports
    """

    list_display = (
        'name',
        'country_preference',
        'education_badge',
        'test_score_display',
        'budget_display',
        'university_matches',
        'counselor_info',
        'status_badge',
        'created_display'
    )

    list_filter = (
        'contact_status',
        'test_type',
        'budget_currency',
        'preferred_country',
        'education_level',
        'assigned_counselor',
        'created_at'
    )

    search_fields = (
        'name',
        'email',
        'education_level',
        'field_of_study',
        'preferred_country',
        'counselor_notes'
    )

    readonly_fields = ('conversation', 'created_at', 'updated_at', 'profile_analytics')

    fieldsets = (
        ('Student Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Academic Background', {
            'fields': ('education_level', 'field_of_study', 'gpa_percentage')
        }),
        ('Test Scores', {
            'fields': ('test_type', 'test_score')
        }),
        ('Preferences', {
            'fields': ('budget_amount', 'budget_currency', 'preferred_country', 'preferred_programs')
        }),
        ('University Recommendations', {
            'fields': ('recommended_universities',)
        }),
        ('Counselor Management', {
            'fields': ('assigned_counselor', 'contact_status', 'counselor_notes')
        }),
        ('System Info', {
            'fields': ('conversation', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('profile_analytics',)
        })
    )

    actions = [
        'update_contact_information',
        'export_profiles_excel',
        'assign_counselor',
        'mark_contacted',
        'generate_university_matches',
        'create_follow_up_report'
    ]

    def country_preference(self, obj):
        """Display preferred country with flag"""
        flags = {
            'USA': '🇺🇸', 'Canada': '🇨🇦', 'UK': '🇬🇧', 'United Kingdom': '🇬🇧',
            'Australia': '🇦🇺', 'Germany': '🇩🇪', 'France': '🇫🇷', 'Europe': '🇪🇺',
            'Netherlands': '🇳🇱', 'Sweden': '🇸🇪', 'Norway': '🇳🇴'
        }
        flag = flags.get(obj.preferred_country, '🌍')
        return format_html('{} {}', flag, obj.preferred_country)
    country_preference.short_description = 'Target Country'

    def education_badge(self, obj):
        """Display education level with appropriate styling"""
        colors = {
            'Bachelor': '#007bff',
            'Master': '#28a745',
            'PhD': '#6f42c1',
            'Diploma': '#fd7e14'
        }

        for level, color in colors.items():
            if level.lower() in obj.education_level.lower():
                return format_html(
                    '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
                    color, obj.education_level
                )

        return obj.education_level
    education_badge.short_description = 'Education'

    def test_score_display(self, obj):
        """Display test score with performance indicator"""
        score_text = f"{obj.test_type} {obj.test_score}"

        try:
            if obj.test_type == 'IELTS':
                score = float(obj.test_score)
                if score >= 7.5:
                    color = '#28a745'  # Excellent
                elif score >= 6.5:
                    color = '#ffc107'  # Good
                else:
                    color = '#dc3545'  # Needs improvement
            elif obj.test_type == 'TOEFL':
                score = int(obj.test_score)
                if score >= 100:
                    color = '#28a745'
                elif score >= 80:
                    color = '#ffc107'
                else:
                    color = '#dc3545'
            else:
                color = '#6c757d'
        except:
            color = '#6c757d'

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, score_text
        )
    test_score_display.short_description = 'Test Score'

    def budget_display(self, obj):
        """Display budget with affordability indicator"""
        budget_text = f"{obj.budget_amount:,} {obj.budget_currency}"

        # Color code based on budget amount (in USD equivalent)
        usd_equivalent = obj.budget_amount
        if obj.budget_currency == 'EUR':
            usd_equivalent *= 1.1
        elif obj.budget_currency == 'GBP':
            usd_equivalent *= 1.25
        elif obj.budget_currency == 'CAD':
            usd_equivalent *= 0.75

        if usd_equivalent >= 40000:
            color = '#28a745'  # High budget
        elif usd_equivalent >= 20000:
            color = '#ffc107'  # Medium budget
        else:
            color = '#dc3545'  # Low budget

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, budget_text
        )
    budget_display.short_description = 'Budget'

    def university_matches(self, obj):
        """Display university match count with details"""
        count = len(obj.recommended_universities) if obj.recommended_universities else 0

        if count == 0:
            return format_html('<span style="color: #dc3545;">No matches</span>')
        elif count <= 3:
            color = '#ffc107'
        else:
            color = '#28a745'

        # Show top university name if available
        top_uni = ''
        if obj.recommended_universities:
            top_uni = obj.recommended_universities[0].get('name', '')[:20]
            if len(top_uni) == 20:
                top_uni += '...'

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;" title="Top: {}">{}</span>',
            color, top_uni, count
        )
    university_matches.short_description = 'Matches'

    def counselor_info(self, obj):
        """Display counselor assignment info"""
        if obj.assigned_counselor:
            return format_html(
                '<strong>{}</strong>',
                obj.assigned_counselor.username
            )
        else:
            return format_html('<span style="color: #dc3545;">Unassigned</span>')
    counselor_info.short_description = 'Counselor'

    def status_badge(self, obj):
        """Display contact status with color coding"""
        colors = {
            'pending': '#ffc107',
            'contacted': '#007bff',
            'in_progress': '#28a745',
            'completed': '#6c757d'
        }
        color = colors.get(obj.contact_status, '#6c757d')

        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_contact_status_display()
        )
    status_badge.short_description = 'Status'

    def created_display(self, obj):
        """Friendly creation date"""
        return obj.created_at.strftime('%m/%d/%Y')
    created_display.short_description = 'Created'

    def profile_analytics(self, obj):
        """Rich profile analytics and insights with modern styling"""
        # Calculate match score based on profile completeness
        completeness = 0
        if obj.education_level: completeness += 20
        if obj.field_of_study: completeness += 15
        if obj.gpa_percentage: completeness += 15
        if obj.test_score: completeness += 20
        if obj.budget_amount: completeness += 15
        if obj.preferred_country: completeness += 15

        score_color = '#28a745' if completeness >= 80 else '#ffc107' if completeness >= 60 else '#dc3545'

        analytics = f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <h3 style="color: white; margin: 0; font-size: 22px; font-weight: 600;">
                    📊 Profile Analytics Dashboard
                </h3>
                <div style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px;">
                    <span style="color: white; font-weight: bold;">Profile Score: {completeness}%</span>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #ffd700;">
                    <h4 style="color: #ffd700; margin: 0 0 10px 0; font-size: 16px;">🎓 Academic Profile</h4>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Education:</strong> {obj.education_level}</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Field:</strong> {obj.field_of_study or 'Not specified'}</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>GPA:</strong> {obj.gpa_percentage or 'Not provided'}</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Test Score:</strong> {obj.test_type} {obj.test_score}</p>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #00d4aa;">
                    <h4 style="color: #00d4aa; margin: 0 0 10px 0; font-size: 16px;">🌍 Preferences</h4>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Budget:</strong> {obj.budget_amount:,} {obj.budget_currency}</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Country:</strong> {obj.preferred_country}</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Programs:</strong> {len(obj.preferred_programs)} selected</p>
                    <p style="color: white; margin: 5px 0; font-size: 14px;"><strong>Universities:</strong> {len(obj.recommended_universities) if obj.recommended_universities else 0} recommended</p>
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #ff6b9d;">
                <h4 style="color: #ff6b9d; margin: 0 0 15px 0; font-size: 16px;">🏫 University Recommendations</h4>
        """

        if obj.recommended_universities:
            for i, uni in enumerate(obj.recommended_universities[:3]):
                rank_badge = f"#{i+1}" if i < 3 else ""
                analytics += f"""
                <div style="
                    background: rgba(255,255,255,0.9);
                    color: #333;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 6px;
                    border-left: 4px solid #007bff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <strong style="color: #007bff; font-size: 15px;">{uni.get('name', 'Unknown University')}</strong>
                            <span style="color: #6c757d; margin-left: 10px;">📍 {uni.get('country', 'Unknown')}</span>
                        </div>
                        {f'<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{rank_badge}</span>' if rank_badge else ''}
                    </div>
                    <div style="margin-top: 5px; font-size: 13px; color: #666;">
                        💰 <strong>Tuition:</strong> {uni.get('tuition', 'Not specified')} |
                        🏆 <strong>Ranking:</strong> {uni.get('ranking', 'Unranked')}
                    </div>
                </div>
                """
        else:
            analytics += '''
            <div style="
                background: rgba(255,255,255,0.1);
                color: #ffd700;
                padding: 15px;
                text-align: center;
                border-radius: 6px;
                border: 1px dashed rgba(255,215,0,0.5);
            ">
                <p style="margin: 0; font-size: 14px;">⚠️ No university recommendations available yet</p>
            </div>
            '''

        # Add profile completion progress bar
        analytics += f"""
            </div>

            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: white; font-size: 14px; font-weight: 600;">Profile Completeness</span>
                    <span style="color: white; font-size: 14px; font-weight: bold;">{completeness}%</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: {score_color}; height: 100%; width: {completeness}%; transition: width 0.3s ease;"></div>
                </div>
            </div>
        </div>
        """

        return format_html(analytics)
    profile_analytics.short_description = 'Analytics'

    # Custom Admin Actions
    def update_contact_information(self, request, queryset):
        """Update missing contact information from conversation data"""
        updated_count = 0
        for profile in queryset:
            # Check if email or phone is missing
            needs_update = False

            if not profile.email and profile.conversation:
                # Try to get email from conversation
                email = (profile.conversation.processed_email or
                        profile.conversation.student_email or
                        profile.conversation.email_response or "").strip()
                if email:
                    profile.email = email
                    needs_update = True

            if not profile.phone and profile.conversation:
                # Try to get phone from conversation
                phone = (profile.conversation.processed_phone or
                        profile.conversation.student_phone or
                        profile.conversation.phone_response or "").strip()
                if phone:
                    profile.phone = phone
                    needs_update = True

            if needs_update:
                profile.save()
                updated_count += 1

        self.message_user(
            request,
            f"Successfully updated contact information for {updated_count} student profiles."
        )
    update_contact_information.short_description = "🔄 Update missing contact info from conversations"

    def export_profiles_excel(self, request, queryset):
        """Export selected student profiles to Excel"""
        data = []
        for profile in queryset:
            data.append({
                'Name': profile.name,
                'Email': profile.email or 'Not provided',
                'Phone': profile.phone or 'Not provided',
                'Education Level': profile.education_level,
                'Field of Study': profile.field_of_study or 'Not specified',
                'GPA': profile.gpa_percentage or 'Not provided',
                'Test Type': profile.test_type,
                'Test Score': profile.test_score,
                'Budget': f"{profile.budget_amount} {profile.budget_currency}",
                'Preferred Country': profile.preferred_country,
                'University Matches': len(profile.recommended_universities) if profile.recommended_universities else 0,
                'Counselor': profile.assigned_counselor.username if profile.assigned_counselor else 'Unassigned',
                'Status': profile.contact_status,
                'Created Date': profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Notes': profile.counselor_notes or 'No notes'
            })

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="student_profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Student Profiles', index=False)
        excel_buffer.seek(0)
        response.write(excel_buffer.getvalue())

        self.message_user(request, f"Successfully exported {len(data)} student profiles.")
        return response

    export_profiles_excel.short_description = "📊 Export profiles to Excel"

    def assign_counselor(self, request, queryset):
        """Assign counselor to selected profiles"""
        # This would typically show a form to select counselor
        # For now, we'll assign to the current user if they're staff
        if request.user.is_staff:
            updated = queryset.update(assigned_counselor=request.user, contact_status='contacted')
            self.message_user(request, f"Assigned {updated} profiles to {request.user.username}")
        else:
            self.message_user(request, "You must be staff to assign profiles", level='ERROR')

    assign_counselor.short_description = "👤 Assign to me as counselor"

    def mark_contacted(self, request, queryset):
        """Mark profiles as contacted"""
        updated = queryset.update(contact_status='contacted')
        self.message_user(request, f"Marked {updated} profiles as contacted.")

    mark_contacted.short_description = "📞 Mark as contacted"

    def generate_university_matches(self, request, queryset):
        """Generate university match report"""
        all_universities = {}
        for profile in queryset:
            if profile.recommended_universities:
                for uni in profile.recommended_universities:
                    name = uni.get('name', 'Unknown')
                    country = uni.get('country', 'Unknown')
                    key = f"{name} ({country})"
                    if key not in all_universities:
                        all_universities[key] = 0
                    all_universities[key] += 1

        # Create report
        sorted_unis = sorted(all_universities.items(), key=lambda x: x[1], reverse=True)

        if sorted_unis:
            top_uni = sorted_unis[0]
            self.message_user(
                request,
                f"University Match Report: {len(sorted_unis)} unique universities. Most popular: {top_uni[0]} ({top_uni[1]} matches)"
            )
        else:
            self.message_user(request, "No university matches found in selected profiles.")

    generate_university_matches.short_description = "📈 Generate match report"

    def create_follow_up_report(self, request, queryset):
        """Create follow-up report for profiles"""
        pending = queryset.filter(contact_status='pending').count()
        contacted = queryset.filter(contact_status='contacted').count()
        in_progress = queryset.filter(contact_status='in_progress').count()
        completed = queryset.filter(contact_status='completed').count()

        self.message_user(
            request,
            f"Follow-up Report: Pending: {pending}, Contacted: {contacted}, In Progress: {in_progress}, Completed: {completed}"
        )

    create_follow_up_report.short_description = "📋 Follow-up report"


# Customize Django Admin Site
admin.site.site_header = 'Scholarport Admin Dashboard'
admin.site.site_title = 'Scholarport Admin'
admin.site.index_title = 'Welcome to Scholarport Administration'

# Add custom CSS for better styling
admin.site.enable_nav_sidebar = True
