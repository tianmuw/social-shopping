# backend/notifications/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回"发给我"的通知，按时间倒序
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    # (1) 获取未读数量 (用于前端 Navbar 红点)
    # URL: /api/v1/notifications/unread_count/
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})

    # (2) 标记某条通知为已读
    # URL: /api/v1/notifications/{id}/read/
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        return Response({'status': 'marked as read'})

    # (3) 标记所有为已读 (一键清除红点)
    # URL: /api/v1/notifications/mark_all_read/
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})