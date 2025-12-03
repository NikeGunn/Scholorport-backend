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
    # List all partners (including inactive)
    path('admin/', views.admin_list_partners, name='admin-list-partners'),

    # Create a new partner
    path('admin/create/', views.admin_create_partner, name='admin-create-partner'),

    # Update a partner
    path('admin/<uuid:partner_id>/', views.admin_update_partner, name='admin-update-partner'),

    # Delete a partner
    path('admin/<uuid:partner_id>/delete/', views.admin_delete_partner, name='admin-delete-partner'),
]
