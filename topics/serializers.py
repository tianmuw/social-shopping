from rest_framework import serializers
from .models import Topic, TopicSubscription


class TopicSerializer(serializers.ModelSerializer):
    # 1. 这是一个只读字段，由 View 中的 annotate 计算得出
    subscribers_count = serializers.IntegerField(read_only=True)

    # 2. 这是一个动态字段，判断当前用户是否已加入
    is_subscribed = serializers.SerializerMethodField()

    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug', 'description', 'subscribers_count', 'is_subscribed', 'posts_count', 'icon', 'banner']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 检查是否存在订阅记录
            return TopicSubscription.objects.filter(user=request.user, topic=obj).exists()
        return False