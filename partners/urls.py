"""
Partners App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    # ==================== Public Endpoints ====================
    # List all active partners (for homepage)
    path('', views.list_partners, name='list-partners'),

    # Get partner details
    path('<uuid:partner_id>/', views.get_partner, name='get-partner'),

    # ==================== Admin Endpoints ====================
    # List all partners (GET) or Create new partner (POST)
    path('admin/', views.admin_partners, name='admin-partners'),

    # Get, Update, or Delete a specific partner
    path('admin/<uuid:partner_id>/', views.admin_partner_detail, name='admin-partner-detail'),
]
