# users/urls.py

from django.urls import path, include

urlpatterns = [
    # 把 djoser 的核心 URL 和 JWT URL 都包含在这里
    # Django 会先检查 djoser.urls，如果找不到，会继续检查 djoser.urls.jwt
    path('', include('djoser.urls')),
    path('', include('djoser.urls.jwt')),
]