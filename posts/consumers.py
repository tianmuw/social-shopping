# backend/posts/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PostConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 从 URL 获取 post_id
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'post_{self.post_id}'

        # 加入帖子组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 接收来自 signal 的新评论消息
    async def send_new_comment(self, event):
        comment = event['comment']
        # 发送给前端
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment': comment
        }))