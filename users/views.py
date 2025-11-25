# backend/users/views.py
from rest_framework import viewsets, permissions, status, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from .models import UserFollow, UserBlock, MerchantProfile
from .serializers import ProfileSerializer, UserSerializer, MerchantProfileSerializer

User = get_user_model()

class ProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    只读视图集，用于查看用户资料和关注/取消关注。
    Lookup field 是 'username' 而不是 'id'，这样 URL 更友好 (/profiles/Mike/)
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'username' # 使用用户名查找

    # 启用搜索和排序
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username']
    ordering_fields = ['followers_count', 'date_joined']
    ordering = ['-followers_count']  # 默认按粉丝数倒序 (即高粉丝数在前)

    def get_queryset(self):
        # 预先计算粉丝数和关注数
        return User.objects.annotate(
            followers_count=Count('followers', distinct=True),
            following_count=Count('following', distinct=True)
        )

    # 动作: 关注/取消关注
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, username=None):
        target_user = self.get_object()
        follower = request.user

        if target_user == follower:
            return Response({'detail': '你不能关注你自己。'}, status=status.HTTP_400_BAD_REQUEST)

        # get_or_create 实现关注
        follow_obj, created = UserFollow.objects.get_or_create(follower=follower, followed=target_user)

        if created:
            return Response({'status': 'followed'}, status=status.HTTP_201_CREATED)
        else:
            # 如果已经关注了，再次点击则是取消关注 (Toggle)
            # 或者你可以像话题那样拆分成 join/leave，这里我们用 toggle 逻辑演示另一种写法
            # 但为了保持一致性，我们还是用 "如果已存在则返回已关注" 或者是 "取消关注"？
            # 让我们模仿 topic 的逻辑：再次请求不删除，而是返回状态。删除用单独逻辑？
            # 不，为了简单，我们这里实现 "Toggle" (切换)：点一下关注，再点一下取消。
            follow_obj.delete()
            return Response({'status': 'unfollowed'}, status=status.HTTP_200_OK)

    # ---------------------------------------------------------
    # 2. 拉黑 / 取消拉黑 (新增)
    # ---------------------------------------------------------
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def block(self, request, username=None):
        target_user = self.get_object()
        blocker = request.user
        if target_user == blocker:
            return Response({'detail': '你不能拉黑你自己。'}, status=status.HTTP_400_BAD_REQUEST)

        # 拉黑逻辑: 创建记录
        block_obj, created = UserBlock.objects.get_or_create(blocker=blocker, blocked=target_user)

        if created:
            # (可选) 强力拉黑: 如果拉黑了，自动取关
            UserFollow.objects.filter(follower=blocker, followed=target_user).delete()
            UserFollow.objects.filter(follower=target_user, followed=blocker).delete()
            return Response({'status': 'blocked'}, status=status.HTTP_201_CREATED)
        else:
            # 如果已经拉黑，再次点击则是取消拉黑
            block_obj.delete()
            return Response({'status': 'unblocked'}, status=status.HTTP_200_OK)

    # ---------------------------------------------------------
    # 3. 获取粉丝列表 (带隐私检查)
    # URL: /api/v1/profiles/{username}/followers/
    # ---------------------------------------------------------
    @action(detail=True, methods=['get'])
    def followers(self, request, username=None):
        target_user = self.get_object()

        # 隐私检查: 如果不是看自己，且对方设置了"不公开粉丝"，则拒绝
        if request.user != target_user and not target_user.is_followers_public:
            return Response({'detail': '该用户的粉丝列表未公开。'}, status=status.HTTP_403_FORBIDDEN)

        # 获取所有关注了 target_user 的人
        followers = User.objects.filter(following__followed=target_user)

        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserSerializer(page, many=True)  # 使用简单的 UserSerializer
            return self.get_paginated_response(serializer.data)

        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)

    # ---------------------------------------------------------
    # 4. 获取关注列表 (带隐私检查)
    # URL: /api/v1/profiles/{username}/following/
    # ---------------------------------------------------------
    @action(detail=True, methods=['get'])
    def following(self, request, username=None):
        target_user = self.get_object()

        # 隐私检查
        if request.user != target_user and not target_user.is_following_public:
            return Response({'detail': '该用户的关注列表未公开。'}, status=status.HTTP_403_FORBIDDEN)

        # 获取所有 target_user 关注的人
        following = User.objects.filter(followers__follower=target_user)

        page = self.paginate_queryset(following)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserSerializer(following, many=True)
        return Response(serializer.data)

class MerchantViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """
    商家接口：
    POST /api/v1/merchants/ -> 提交申请
    GET  /api/v1/merchants/me/ -> 查看我的状态
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MerchantProfileSerializer

    def get_queryset(self):
        return MerchantProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 检查是否已经申请过
        if MerchantProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError("您已经提交过商家申请，请勿重复提交。")
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            merchant = MerchantProfile.objects.get(user=request.user)
            serializer = self.get_serializer(merchant)
            return Response(serializer.data)
        except MerchantProfile.DoesNotExist:
            # 如果没申请过，返回 404，前端据此显示表单
            return Response({'detail': '尚未申请'}, status=status.HTTP_404_NOT_FOUND)