"""
Jobs/Careers App URL Configuration

URL patterns for the Jobs API endpoints.
"""
from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # ==================== Public Endpoints ====================
    # List all active jobs
    path('', views.list_jobs, name='list-jobs'),

    # ==================== Admin Endpoints ====================
    # Admin paths MUST come before slug pattern to avoid conflicts
    # List all jobs (admin - includes inactive)
    path('admin/', views.admin_list_jobs, name='admin-list-jobs'),

    # Create new job
    path('admin/create/', views.admin_create_job, name='admin-create-job'),

    # Get job by ID (admin)
    path('admin/<uuid:job_id>/', views.admin_get_job, name='admin-get-job'),

    # Update job by ID (admin)
    path('admin/<uuid:job_id>/update/', views.admin_update_job, name='admin-update-job'),

    # Delete job by ID (admin)
    path('admin/<uuid:job_id>/delete/', views.admin_delete_job, name='admin-delete-job'),

    # ==================== Public Endpoints ====================
    # Get job by slug (must come LAST to avoid matching 'admin' as a slug)
    path('<slug:slug>/', views.get_job_by_slug, name='get-job-by-slug'),
]
