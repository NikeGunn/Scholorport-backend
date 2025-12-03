"""
Contact App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    # ==================== Public Endpoints ====================
    # Submit contact form
    path('', views.submit_contact_form, name='submit-contact'),

    # ==================== Admin Endpoints ====================
    # List all submissions
    path('admin/', views.admin_list_submissions, name='admin-list-submissions'),

    # Get submission statistics
    path('admin/stats/', views.admin_stats, name='admin-stats'),

    # Get submission details
    path('admin/<uuid:submission_id>/', views.admin_get_submission, name='admin-get-submission'),

    # Mark as read
    path('admin/<uuid:submission_id>/read/', views.admin_mark_read, name='admin-mark-read'),

    # Update submission (notes)
    path('admin/<uuid:submission_id>/update/', views.admin_update_submission, name='admin-update-submission'),

    # Delete submission
    path('admin/<uuid:submission_id>/delete/', views.admin_delete_submission, name='admin-delete-submission'),
]
