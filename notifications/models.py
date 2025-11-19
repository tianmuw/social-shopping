# backend/notifications/models.py
from django.db import models
from django.conf import settings


class Notification(models.Model):
    # 通知的类型
    TYPE_CHOICES = (
        ('follow', '关注了你'),
        ('comment', '评论了你的帖子'),
        ('reply', '回复了你的评论'),
        ('vote', '赞了你的帖子'),  # 可选
    )

    # 接收者 (谁应该看到这条通知)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')

    # 触发者 (谁干的，比如 Mike)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='triggered_notifications')

    # 类型
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # 关联的帖子 ID (可选，用于跳转)
    post_id = models.IntegerField(null=True, blank=True)

    # 是否已读
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # 最新通知在最前

    def __str__(self):
        return f"{self.actor} {self.notification_type} -> {self.recipient}"