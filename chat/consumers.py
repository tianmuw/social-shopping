# backend/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. 获取 URL 中的 room_name (即 conversation_id)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        # 2. 检查用户是否已登录 (Channels 的 AuthMiddlewareStack 会自动填充 scope['user'])
        if self.user.is_anonymous:
            await self.close()
            return

        # 3. 加入房间组 (Redis Channel Layer)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 收到 WebSocket 消息 (来自前端)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 1. 保存消息到数据库 (必须是同步操作转异步)
        saved_message = await self.save_message(self.room_name, self.user, message)

        if saved_message:
            # 2. 广播消息给房间组
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.user.username,
                    'avatar': self.user.avatar.url if self.user.avatar else None,
                    'created_at': saved_message.created_at.isoformat()
                }
            )

    # 处理来自房间组的消息 (广播)
    async def chat_message(self, event):
        # 发送给 WebSocket (前端)
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'avatar': event['avatar'],
            'created_at': event['created_at']
        }))

    # 辅助方法: 保存消息到数据库
    @database_sync_to_async
    def save_message(self, conversation_id, user, content):
        try:
            conversation = Conversation.objects.get(pk=conversation_id)
            # 只有参与者才能发消息
            if user not in conversation.participants.all():
                return None

            message = Message.objects.create(
                conversation=conversation,
                sender=user,
                content=content
            )
            # 更新会话的 updated_at，以便列表排序
            conversation.save()
            return message
        except Conversation.DoesNotExist:
            return None