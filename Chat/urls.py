from django.urls import path
from . import views

urlpatterns = [
    path('test-chat', views.TestChat)
]