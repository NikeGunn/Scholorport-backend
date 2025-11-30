"""
Booking App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # ==================== Counselor Endpoints ====================
    # List all active counselors
    path('counselors/', views.list_counselors, name='list-counselors'),

    # Get counselor details
    path('counselors/<int:counselor_id>/', views.get_counselor, name='get-counselor'),

    # Get available slots for a counselor
    path('counselors/<int:counselor_id>/slots/', views.get_counselor_slots, name='counselor-slots'),

    # Set counselor availability (admin)
    path('counselors/<int:counselor_id>/availability/', views.set_counselor_availability, name='set-availability'),

    # Delete counselor availability (admin)
    path('counselors/<int:counselor_id>/availability/<int:availability_id>/',
         views.delete_counselor_availability, name='delete-availability'),

    # ==================== Booking Endpoints ====================
    # Create a new booking
    path('sessions/', views.create_booking, name='create-booking'),

    # Get bookings by email
    path('my-bookings/', views.list_bookings_by_email, name='my-bookings'),

    # Get booking details
    path('sessions/<uuid:booking_id>/', views.get_booking, name='get-booking'),

    # Update booking
    path('sessions/<uuid:booking_id>/update/', views.update_booking, name='update-booking'),

    # Cancel booking
    path('sessions/<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel-booking'),

    # Verify booking (email verification)
    path('sessions/<uuid:booking_id>/verify/', views.verify_booking, name='verify-booking'),

    # Reschedule booking (same as update)
    path('sessions/<uuid:booking_id>/reschedule/', views.update_booking, name='reschedule-booking'),

    # Submit feedback
    path('sessions/<uuid:booking_id>/feedback/', views.submit_feedback, name='submit-feedback'),

    # ==================== Admin Endpoints ====================
    # List all bookings (admin)
    path('admin/sessions/', views.admin_list_bookings, name='admin-list-bookings'),

    # Update booking status (admin)
    path('admin/sessions/<uuid:booking_id>/', views.admin_update_booking_status, name='admin-update-status'),

    # Booking statistics
    path('admin/stats/', views.booking_stats, name='booking-stats'),
]