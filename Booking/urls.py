from django.urls import path
from . import views

urlpatterns = [
    path('create-booking/', views.create_booking, name='create-booking'),
    path('bookings/', views.get_bookings, name='bookings'),
    path('<int:booking_id>/', views.get_booking_id, name='get_booking'),
]