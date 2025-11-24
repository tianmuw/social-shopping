# backend/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import UserFollow
from posts.models import Comment, Vote
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
        # (!!!) 新增逻辑：同时广播给"帖子频道" (解决问题 1 的一部分) (!!!)
        # 我们在这里顺便把"新评论"广播给正在看帖子的所有人
        channel_layer = get_channel_layer()
        # 假设帖子频道的组名是 "post_{id}"
        # 我们需要序列化评论数据，这里简单构造一下，或者引入 Serializer
        # 为了避免循环导入，我们简单构造一个字典
        comment_data = {
            "id": instance.id,
            "content": instance.content,
            "created_at": instance.created_at.isoformat(),
            "author": {
                "username": instance.author.username,
                "avatar": instance.author.avatar.url if instance.author.avatar else None
            },
            "replies": []  # 新评论肯定没有回复
        }

        async_to_sync(channel_layer.group_send)(
            f"post_{instance.post.id}",
            {
                "type": "send_new_comment",  # 对应 Consumer 的方法
                "comment": comment_data
            }
        )

        # (原有的通知逻辑保持不变)
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

# 监听点赞
@receiver(post_save, sender=Vote)
def create_vote_notification(sender, instance, created, **kwargs):
    # 只在创建且是"顶"(1)的时候发通知，"踩"(-1)通常不发通知
    if created and instance.vote_type == 1:
        # 不要给自己发通知
        if instance.post.author != instance.user:
            notif = Notification.objects.create(
                recipient=instance.post.author,
                actor=instance.user,
                notification_type='vote', # 确保 models.py 的 TYPE_CHOICES 里有 'vote'
                post_id=instance.post.id
            )
            push_notification(notif)