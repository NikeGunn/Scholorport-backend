"""
URL patterns for the chat app.

This module defines all the API endpoints for the Scholarport backend.
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Core Chat API Endpoints
    path('start/', views.start_conversation, name='start_conversation'),
    path('send/', views.send_message, name='send_message'),
    path('consent/', views.handle_data_consent, name='handle_data_consent'),
    path('conversation/<str:session_id>/', views.get_conversation_history, name='get_conversation_history'),

    # University API Endpoints
    path('universities/', views.get_universities, name='get_universities'),
    path('universities/<int:university_id>/', views.get_university_details, name='get_university_details'),

    # Admin Panel API Endpoints
    path('admin/stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    path('admin/profiles/', views.admin_get_student_profiles, name='admin_get_student_profiles'),
    path('admin/export/', views.admin_export_excel, name='admin_export_excel'),

    # Add this line to your urlpatterns in chat/urls.py
    path('admin/firebase-export/', views.admin_export_firebase_data, name='admin_firebase_export'),

    # Health Check
    path('health/', views.health_check, name='health_check'),
]