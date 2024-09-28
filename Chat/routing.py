from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/message/<str:room_id>/', ChatConsumer.as_asgi()),
]