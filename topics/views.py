from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import Topic, TopicSubscription
from .serializers import TopicSerializer


class TopicViewSet(viewsets.ModelViewSet):
    #自动计算订阅人数 (subscribers_count)
    queryset = Topic.objects.annotate(
        subscribers_count=Count('subscriptions')
    ).order_by('-created_at')

    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    #加入话题
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, slug=None):
        topic = self.get_object()
        user = request.user

        # get_or_create 防止重复创建
        subscription, created = TopicSubscription.objects.get_or_create(user=user, topic=topic)

        if created:
            return Response({'status': 'joined', 'subscribers_count': topic.subscriptions.count()},
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'already_joined'}, status=status.HTTP_200_OK)

    #退出话题
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, slug=None):
        topic = self.get_object()
        user = request.user

        try:
            sub = TopicSubscription.objects.get(user=user, topic=topic)
            sub.delete()
            return Response({'status': 'left', 'subscribers_count': topic.subscriptions.count()},
                            status=status.HTTP_200_OK)
        except TopicSubscription.DoesNotExist:
            return Response({'status': 'not_joined'}, status=status.HTTP_400_BAD_REQUEST)