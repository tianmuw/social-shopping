# backend/users/views.py
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import UserFollow
from .serializers import ProfileSerializer

User = get_user_model()

class ProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """
    只读视图集，用于查看用户资料和关注/取消关注。
    Lookup field 是 'username' 而不是 'id'，这样 URL 更友好 (/profiles/Mike/)
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'username' # (!!!) 关键：使用用户名查找

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