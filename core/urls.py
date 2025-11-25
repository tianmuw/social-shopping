"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# 导入我们 app 里的 router
# 我们需要先导入 viewset，而不是 router
from topics.views import TopicViewSet
from posts.views import PostViewSet
from users.views import ProfileViewSet, MerchantViewSet
from chat.views import ConversationViewSet
from notifications.views import NotificationViewSet


# 1. 创建一个 V1 版本的总路由器
router_v1 = DefaultRouter()

# 2. 把我们所有的 ViewSet 注册到这个总路由器上
router_v1.register(r'topics', TopicViewSet, basename='topic')
router_v1.register(r'posts', PostViewSet, basename='post')
router_v1.register(r'profiles', ProfileViewSet, basename='profile')
router_v1.register(r'chat/conversations', ConversationViewSet, basename='conversation')
router_v1.register(r'notifications', NotificationViewSet, basename='notification')
router_v1.register(r'merchants', MerchantViewSet, basename='merchant')


# 3. 定义主 URL 模式
urlpatterns = [
    # Django Admin 后台
    path('admin/', admin.site.urls),

    # 把所有 /api/v1/ 开头的 URL 都交给我们的总路由器处理
    path('api/v1/', include(router_v1.urls)),

    # 我们的认证 API (Login, Register, etc.)
    # Djoser 会自动生成 /auth/token, /auth/users, /auth/users/me 等
    path('api/v1/auth/', include('users.urls')),  # <-- 这是修正后的一行

    # AI 路由
    path('api/v1/ai/', include('ai_agent.urls')),

    # (!!!) 新增这一行 (!!!)
    # 这将为我们提供 /api-auth/login/ 和 /api-auth/logout/
    # 专门用于在浏览器中测试 API
    path('api-auth/', include('rest_framework.urls')),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
