"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# backend/core/asgi.py
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django_asgi_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JwtAuthMiddleware
from chat import routing as chat_routing
from notifications import routing as notifications_routing


application = ProtocolTypeRouter({
    # 1. 如果是 HTTP 请求，交给 Django 正常处理
    "http": django_asgi_app,

    # 2. 如果是 WebSocket 请求，交给 Channels 处理
    # AuthMiddlewareStack 会自动把用户 user 放入 scope 中
    "websocket": JwtAuthMiddleware(
        URLRouter(
            # 合并路由列表
            chat_routing.websocket_urlpatterns +
            notifications_routing.websocket_urlpatterns
        )
    ),
})
