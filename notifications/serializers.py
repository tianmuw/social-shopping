# backend/notifications/serializers.py
from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer  # 复用我们现有的用户序列化器


class NotificationSerializer(serializers.ModelSerializer):
    # 嵌套显示触发者的信息 (头像、用户名)
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'actor', 'post_id', 'is_read', 'created_at']