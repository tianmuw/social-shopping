from rest_framework import viewsets, permissions
from .models import Topic
from .serializers import TopicSerializer


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    一个只读的 ViewSet，用于查看话题列表和详情。
    我们不希望任何人都能通过 API 随便创建或删除话题
    (创建话题应该在 /admin 后台由管理员操作)
    """
    queryset = Topic.objects.all().order_by('-created_at')  # API 返回所有话题，按创建时间倒序
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]  # 允许任何人查看

    # 这个 lookup_field 告诉 DRF
    # 当用户访问 /api/v1/topics/huashan-travel/ 时
    # 应该用 'slug' 字段去查找，而不是用 'id'
    lookup_field = 'slug'