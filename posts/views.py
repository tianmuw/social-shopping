from rest_framework import viewsets, permissions, mixins
from .models import Post
from .serializers import (
    PostListRetrieveSerializer, # 用于 "读"
    PostCreateSerializer      # 用于 "写"
)


# class PostViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     一个只读的 ViewSet，用于查看帖子列表 (List) 和详情 (Retrieve)。
#     """
#     # 关键：我们在这里进行一个重要的数据库性能优化
#     # .select_related(...) 会"预加载" 'author', 'topic', 'product'
#     # 这样 Django 就不会在循环中为每个 Post 单独查询数据库
#     # 这可以把 101 次数据库查询（N+1 问题）减少到 1 次！
#     queryset = Post.objects.all().select_related(
#         'author', 'topic', 'product'
#     ).order_by('-created_at')  # 按创建时间倒序
#
#     serializer_class = PostListRetrieveSerializer
#     permission_classes = [permissions.AllowAny]  # 任何人都可以看

class PostViewSet(
    mixins.CreateModelMixin,   # <-- 允许 "创建" (POST)
    mixins.ListModelMixin,     # <-- 允许 "列表" (GET)
    mixins.RetrieveModelMixin, # <-- 允许 "详情" (GET)
    viewsets.GenericViewSet
):
    """
    一个支持 读、写 的 ViewSet。
    - GET /api/v1/posts/ -> 列表
    - GET /api/v1/posts/{id}/ -> 详情
    - POST /api/v1/posts/ -> 创建
    """

    # 权限：
    # - 只有登录用户才能"创建" (IsAuthenticated)
    # - 任何人都可以"读取" (AllowAny)
    # DRF 的 IsAuthenticatedOrReadOnly 会自动处理
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # 我们需要根据不同的操作 (action) 使用不同的序列化器
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer

        # 默认 (list, retrieve)
        return PostListRetrieveSerializer

    def get_queryset(self):
        # 保持我们之前的优化
        return Post.objects.all().select_related(
            'author', 'topic', 'product'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        # 当调用 .save() 时，把 'request' 传递给序列化器
        # 这样 PostCreateSerializer 里的 self.context['request'] 就能拿到了
        serializer.save()