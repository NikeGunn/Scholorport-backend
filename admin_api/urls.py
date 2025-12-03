"""
Admin API URL Configuration

URL patterns for the Admin API endpoints.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'admin_api'

urlpatterns = [
    # Authentication
    path('auth/login/', views.admin_login, name='admin-login'),
    path('auth/logout/', views.admin_logout, name='admin-logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', views.get_current_user, name='current-user'),
    path('auth/profile/', views.update_profile, name='update-profile'),
    path('auth/change-password/', views.change_password, name='change-password'),

    # Dashboard
    path('dashboard/', views.dashboard_overview, name='dashboard-overview'),
    path('dashboard/activity/', views.recent_activity, name='recent-activity'),
    path('dashboard/analytics/', views.analytics_data, name='analytics-data'),
    path('dashboard/pending/', views.pending_items, name='pending-items'),

    # User Management
    path('users/', views.list_users, name='list-users'),
    path('users/create/', views.create_user, name='create-user'),
    path('users/<int:user_id>/', views.get_user, name='get-user'),
    path('users/<int:user_id>/update/', views.update_user, name='update-user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset-password'),

    # Global Search
    path('search/', views.global_search, name='global-search'),
]
