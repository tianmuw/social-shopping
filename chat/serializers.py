# backend/chat/serializers.py
from rest_framework import serializers
from .models import Conversation, Message
from users.serializers import UserSerializer  # 复用你的用户序列化器


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    # 获取最后一条消息 (用于在列表页显示预览)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None