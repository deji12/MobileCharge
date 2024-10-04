from django.urls import path
from . import views

urlpatterns = [
    path('get-drivers/', views.get_drivers)
]