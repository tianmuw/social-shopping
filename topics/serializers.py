from rest_framework import serializers
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    """
    Topic 模型的序列化器
    """

    class Meta:
        model = Topic  # 告诉序列化器它对应的是 Topic 模型

        # 告诉它需要"翻译"哪些字段
        # 我们希望 API 返回这些信息
        fields = ['id', 'name', 'slug', 'description', 'subscribers_count']

    # 我们在 ModelSerializer 之外额外定义一个字段
    # Model 里没有 'subscribers_count'，但我们可以自己算出来
    subscribers_count = serializers.SerializerMethodField()

    def get_subscribers_count(self, obj):
        # 'obj' 就是当前的 Topic 实例
        # .count() 是一个高效的数据库操作
        return obj.subscribers.count()