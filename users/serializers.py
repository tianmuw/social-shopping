from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User

class UserCreateSerializer(BaseUserCreateSerializer):
    """
    用于"注册"的序列化器
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        # 我们允许用户在注册时只提交这三个字段
        fields = ('id', 'username', 'email', 'password')

class UserSerializer(BaseUserSerializer):
    """
    用于"读取"用户信息的序列化器 (例如 /auth/users/me/)
    """
    class Meta(BaseUserSerializer.Meta):
        model = User
        # 我们只暴露这些"安全"的字段，绝不能暴露 password_hash
        fields = ('id', 'username', 'email')