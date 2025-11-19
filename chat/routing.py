# backend/chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://localhost:8000/ws/chat/1/
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]