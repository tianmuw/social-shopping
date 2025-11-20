# backend/notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        # 只有登录用户才能连接通知通道
        if self.user.is_anonymous:
            await self.close()
        else:
            # 创建一个专属的组名: notify_user_{id}
            self.group_name = f"notify_user_{self.user.id}"

            # 加入组
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # 处理来自信号 (Signal) 的消息
    async def send_notification(self, event):
        # 将消息转发给前端 WebSocket
        await self.send(text_data=json.dumps(event['content']))