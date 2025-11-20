# backend/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import UserFollow
from posts.models import Comment
from chat.models import Message
from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# 辅助函数：推送消息到 WebSocket
def push_notification(notification):
    channel_layer = get_channel_layer()
    group_name = f"notify_user_{notification.recipient.id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",  # 对应 Consumer 中的方法名
            "content": {
                "type": "new_notification",
                "notification_type": notification.notification_type,
                "actor_name": notification.actor.username,
                # 可以在这里添加更多前端需要的数据，比如 avatarUrl
            }
        }
    )

@receiver(post_save, sender=UserFollow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        notif = Notification.objects.create(
            recipient=instance.followed,
            actor=instance.follower,
            notification_type='follow'
        )
        push_notification(notif)  # 推送


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        recipient = None
        if instance.parent:
            if instance.parent.author != instance.author:
                recipient = instance.parent.author
                notif = Notification.objects.create(
                    recipient=instance.parent.author,
                    actor=instance.author,
                    notification_type='reply',
                    post_id=instance.post.id
                )
                push_notification(notif)  # 推送
        else:
            if instance.post.author != instance.author:
                recipient = instance.post.author
                notif = Notification.objects.create(
                    recipient=instance.post.author,
                    actor=instance.author,
                    notification_type='comment',
                    post_id=instance.post.id
                )
                push_notification(notif)  # 推送


# 监听私信
@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        # 找到接收者（会话中的另一个人）
        # 假设是双人聊天：排除发送者，剩下的就是接收者
        recipient = instance.conversation.participants.exclude(id=instance.sender.id).first()

        if recipient:
            notif = Notification.objects.create(
                recipient=recipient,
                actor=instance.sender,
                notification_type='message',
                # 我们这里 post_id 没用，可以不填，或者你可以复用这个字段存 conversation_id
                # 但为了简单，我们稍后在前端处理跳转逻辑
            )
            push_notification(notif)  # 推送