# backend/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import UserFollow
from posts.models import Comment
from .models import Notification

# 1. 监听"关注"事件
@receiver(post_save, sender=UserFollow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        # instance.follower 关注了 instance.followed
        Notification.objects.create(
            recipient=instance.followed,
            actor=instance.follower,
            notification_type='follow'
        )

# 2. 监听"评论"事件
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        # 如果有 parent，说明是"回复"
        if instance.parent:
            # 不要给自己发通知
            if instance.parent.author != instance.author:
                Notification.objects.create(
                    recipient=instance.parent.author,
                    actor=instance.author,
                    notification_type='reply',
                    post_id=instance.post.id
                )
        # 否则是"顶级评论"
        else:
            if instance.post.author != instance.author:
                Notification.objects.create(
                    recipient=instance.post.author,
                    actor=instance.author,
                    notification_type='comment',
                    post_id=instance.post.id
                )