# backend/chat/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    处理会话列表和历史消息
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # 只返回当前用户参与的会话，按更新时间倒序
        return self.request.user.conversations.all().order_by('-updated_at')

    # 动作: 获取某个会话的历史消息
    # URL: /api/v1/chat/conversations/{id}/messages/
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        # 分页获取消息
        messages = conversation.messages.all().order_by('created_at')
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    # 动作: 开始一个新会话 (或获取已有会话)
    # URL: /api/v1/chat/conversations/start/?username=Mike
    @action(detail=False, methods=['post'])
    def start(self, request):
        target_username = request.data.get('username')
        if not target_username:
            return Response({'detail': '必须提供 username'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if target_user == request.user:
            return Response({'detail': '不能和自己聊天'}, status=status.HTTP_400_BAD_REQUEST)

        # 查找是否已经存在这两个人的私聊
        # 这是一个比较复杂的查询: 找到一个 conversation，它的 participants 刚好包含这两个人
        # 这里为了简化 MVP，我们查找 "包含我且包含他" 的会话
        # (严谨的逻辑应该确保只有这两个人，但在 MVP 中我们假设只做私聊)
        me = request.user
        conversation = Conversation.objects.filter(participants=me).filter(participants=target_user).first()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(me, target_user)

        serializer = self.get_serializer(conversation)
        return Response(serializer.data)