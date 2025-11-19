from rest_framework import viewsets, permissions, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, IntegerField, Value, Count
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .models import Post, Vote, Comment
from .serializers import (
    PostListRetrieveSerializer,
    PostCreateSerializer,
    VoteSerializer,
    CommentSerializer
)
from django.db.models import Q
from users.models import UserBlock

class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # 指定我们使用的所有 Backend
    filter_backends = [DjangoFilterBackend, OrderingFilter, filters.SearchFilter]

    filterset_fields = ['topic__slug']

    # 允许 API 用户通过 ?ordering=score 或 ?ordering=-score 来排序
    ordering_fields = ['created_at', 'score']

    search_fields = ['title', 'content']

    # 如果用户不提供 ordering 参数, 默认按 "最新" 排序
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        # 如果是 'vote' 动作，使用 VoteSerializer
        if self.action == 'vote':
            return VoteSerializer

        if self.action in ['create_comment', 'list_comments']:
            return CommentSerializer
        return PostListRetrieveSerializer

    # 新增：我们需要把 'request' 传递给序列化器
    # 这样 'get_user_vote' 才能拿到 request.user
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get_queryset(self):
        # 1. 预加载 (Prefetch) votes，为 get_user_vote 解决 N+1 问题
        queryset = Post.objects.prefetch_related('votes')

        # 2. 预加载 (Select) 关联对象
        queryset = queryset.select_related('author', 'topic', 'product')

        # 3. (新) 注解 (Annotate) score 字段
        #    Coalesce(Sum('...'), 0) 确保没有投票的帖子返回 0 而不是 None
        queryset = queryset.annotate(
            score=Coalesce(Sum('votes__vote_type'), 0, output_field=IntegerField()),
            comments_count=Coalesce(Count('comments', distinct=True), 0, output_field=IntegerField())
        )

        # 4. 拉黑过滤逻辑
        user = self.request.user
        if user.is_authenticated:
            # A. 我拉黑的人 (我不看他们的帖子)
            # blocking__blocked_id 指的是 UserBlock 表中 blocker=我 的记录里的 blocked_id
            blocked_users = UserBlock.objects.filter(blocker=user).values_list('blocked_id', flat=True)

            # B. 拉黑我的人 (他们不希望我看他们的帖子 - 可选，通常双向屏蔽是标准做法)
            blocking_me_users = UserBlock.objects.filter(blocked=user).values_list('blocker_id', flat=True)

            # C. 执行排除
            queryset = queryset.exclude(author__id__in=blocked_users)
            queryset = queryset.exclude(author__id__in=blocking_me_users)

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    # 核心：我们新的 "vote" 动作
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """
        为帖子投票。
        发送 {'vote_type': 1} (顶) 或 {'vote_type': -1} (踩)
        """
        post = self.get_object()  # 获取当前帖子
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_type = serializer.validated_data['vote_type']

        try:
            # 1. 检查用户是否已经投过票
            vote = Vote.objects.get(post=post, user=user)

            if vote.vote_type == vote_type:
                # 2. 如果用户点击了同一个按钮 (例如 顶 -> 顶)
                #    我们就删除这个投票 (取消投票)
                vote.delete()
                status_code = status.HTTP_200_OK  # 204 = No Content
            else:
                # 3. 如果用户改变了投票 (例如 顶 -> 踩)
                #    我们就更新投票
                vote.vote_type = vote_type
                vote.save()
                status_code = status.HTTP_200_OK  # 200 = OK

        except Vote.DoesNotExist:
            # 4. 如果用户之前没投过票
            #    我们就创建一个新投票
            Vote.objects.create(post=post, user=user, vote_type=vote_type)
            status_code = status.HTTP_201_CREATED  # 201 = Created

        # 5. 重新计算帖子的总分并返回给前端
        new_score = post.votes.aggregate(
            total=Coalesce(Sum('vote_type'), 0, output_field=IntegerField())
        ).get('total')

        return Response({'score': new_score}, status=status_code)

        # (!!!) 新增动作 1: GET /api/v1/posts/{id}/comments/ (!!!)
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def list_comments(self, request, pk=None):
        """
        获取一个帖子的所有评论
        """
        post = self.get_object()  # 获取当前帖子

        # (关键) 我们只选择"顶级"评论 (parent=None)
        # 我们的 RecursiveCommentSerializer 会自动处理所有子回复
        queryset = post.comments.filter(parent__isnull=True).order_by('created_at')

        # (新) DRF 提供了简单的分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # (!!!) 新增动作 2: POST /api/v1/posts/{id}/comments/ (!!!)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_comment(self, request, pk=None):
        """
        为帖子发布一个新评论 (或回复一个已有评论)

        Body (顶级评论):
        { "content": "这是个好帖子!" }

        Body (回复 ID=10 的评论):
        { "content": "我同意!", "parent": 10 }
        """
        post = self.get_object()  # 获取当前帖子
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 检查 'parent' 是否真的属于这个 'post'
        # (防止有人把评论A 回复到 帖子B 下面)
        parent_obj = serializer.validated_data.get('parent')
        if parent_obj and parent_obj.post != post:
            return Response(
                {'detail': '回复的父评论不属于当前帖子。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # (关键) 'save()' 会自动调用 CommentSerializer 的 create()
        # 我们需要手动把 'author' 和 'post' 传进去
        serializer.save(author=user, post=post)

        # 返回新创建的评论 (包含嵌套的作者)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def following(self, request):
        """
        获取"关注流"：只返回我关注的用户发布的帖子，或我加入的话题下的帖子。
        URL: /api/v1/posts/following/
        """
        user = request.user

        # 1. 获取我关注的用户 ID 列表
        # UserFollow 模型中: follower=我, related_name='following'
        # 我们需要取出的字段是 'followed' (被关注的人)
        followed_user_ids = user.following.values_list('followed', flat=True)

        # 2. 获取我加入的话题 ID 列表
        # TopicSubscription 模型中: user=我, related_name='topic_subscriptions'
        # 我们需要取出的字段是 'topic'
        joined_topic_ids = user.topic_subscriptions.values_list('topic', flat=True)

        # 3. 核心过滤逻辑: (作者是我关注的人) OR (话题是我加入的)
        queryset = self.get_queryset().filter(
            Q(author__in=followed_user_ids) | Q(topic__in=joined_topic_ids)
        ).distinct()  # distinct() 去重，防止同一篇帖子因为既关注了人又加入了话题而出现两次

        # 4. 支持分页 (如果开启了分页)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)