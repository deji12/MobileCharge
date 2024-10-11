from django.urls import path
from . import views

urlpatterns = [
    path('create-booking/', views.create_booking, name='create-booking'),
    path('bookings/<str:booking_status>/', views.get_bookings, name='bookings'),
    path('<int:booking_id>/', views.get_booking, name='get_booking'),
    path('update-booking-status/<int:invoice_id>/', views.update_booking_status),
]