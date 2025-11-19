# backend/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import UserFollow
from posts.models import Comment
from chat.models import Message  # (!!!) 导入 Message
from .models import Notification


@receiver(post_save, sender=UserFollow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.followed,
            actor=instance.follower,
            notification_type='follow'
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        if instance.parent:
            if instance.parent.author != instance.author:
                Notification.objects.create(
                    recipient=instance.parent.author,
                    actor=instance.author,
                    notification_type='reply',
                    post_id=instance.post.id
                )
        else:
            if instance.post.author != instance.author:
                Notification.objects.create(
                    recipient=instance.post.author,
                    actor=instance.author,
                    notification_type='comment',
                    post_id=instance.post.id
                )


# 监听私信
@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        # 找到接收者（会话中的另一个人）
        # 假设是双人聊天：排除发送者，剩下的就是接收者
        recipient = instance.conversation.participants.exclude(id=instance.sender.id).first()

        if recipient:
            Notification.objects.create(
                recipient=recipient,
                actor=instance.sender,
                notification_type='message',
                # 我们这里 post_id 没用，可以不填，或者你可以复用这个字段存 conversation_id
                # 但为了简单，我们稍后在前端处理跳转逻辑
            )