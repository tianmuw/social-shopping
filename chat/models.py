# backend/chat/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    代表一个聊天会话 (例如: Frank 和 Mike 的聊天)
    """
    # 参与者 (多对多，因为一个会话有2个或多个人，一个人也有多个会话)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='conversations'
    )
    # 最后更新时间 (用于排序，把最近聊天的排在前面)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"

class Message(models.Model):
    """
    代表一条消息
    """
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # 按时间正序排列 (旧 -> 新)

    def __str__(self):
        return f"Message {self.id} by {self.sender}"