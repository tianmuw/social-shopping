# backend/notifications/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://localhost:8000/ws/notifications/
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]