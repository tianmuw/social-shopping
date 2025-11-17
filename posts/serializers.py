from rest_framework import serializers
from .models import Post, AssociatedProduct
from users.models import User
from topics.models import Topic


# 我们需要创建几个"微型"的只读序列化器，用于嵌套

class PostUserSerializer(serializers.ModelSerializer):
    """用于 Post 作者的"微型"序列化器"""

    class Meta:
        model = User
        fields = ['id', 'username']


class PostTopicSerializer(serializers.ModelSerializer):
    """用于 Post 话题的"微型"序列化器"""

    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    """用于关联商品的序列化器"""

    class Meta:
        model = AssociatedProduct
        # 我们显示所有商品信息
        fields = [
            'original_url',
            'product_title',
            'product_image_url',
            'product_price',
            'scrape_status'
        ]


# --- 这是我们的"主"序列化器 ---

class PostListRetrieveSerializer(serializers.ModelSerializer):
    """
    用于"读取"(List/Retrieve)帖子的序列化器
    它会"嵌套"显示 author, topic 和 product
    """
    # 1. 覆盖 'author' 字段，使用我们自定义的 PostUserSerializer
    author = PostUserSerializer(read_only=True)

    # 2. 覆盖 'topic' 字段
    topic = PostTopicSerializer(read_only=True)

    # 3. 覆盖 'product' 字段
    #    (我们在 Post 模型里把 OneToOne 字段命名为 'product')
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Post
        # 在 fields 中包含我们"覆盖"后的字段
        fields = [
            'id',
            'title',
            'content',
            'view_count',
            'created_at',
            'author',  # 嵌套的作者信息
            'topic',  # 嵌套的话题信息
            'product',  # 嵌套的商品信息
        ]

# posts/serializers.py (在文件底部追加)

class PostCreateSerializer(serializers.ModelSerializer):
    """
    用于"创建"(POST)帖子的序列化器
    """
    # 我们需要用户手动提交 product_url 和 topic (用 slug)
    product_url = serializers.URLField(write_only=True, max_length=1024)
    topic = serializers.SlugRelatedField(
        slug_field='slug', # 用户将提交 'huashan-travel'
        queryset=Topic.objects.all(), # Django 会从这里查找
        write_only=True
    )

    class Meta:
        model = Post
        fields = [
            'title',
            'content',
            'topic',       # 这个是 write_only
            'product_url', # 这个是 write_only
        ]

    def create(self, validated_data):
        # 1. 从 validated_data 中分离出 product_url 和 topic
        #    'pop' 会删除它们，因为 'Post' 模型里没有这两个字段
        product_url = validated_data.pop('product_url')
        topic = validated_data.pop('topic')

        # 2. 获取当前登录的用户 (Serializer 会自动从 view 接收)
        user = self.context['request'].user

        # 3. 创建 Post 实例
        #    (我们把 'author' 和 'topic' 手动加回去)
        post = Post.objects.create(
            author=user,
            topic=topic,
            **validated_data
        )

        # 4. 创建关联的 Product 实例
        product = AssociatedProduct.objects.create(
            post=post,
            original_url=product_url,
            scrape_status=AssociatedProduct.ScrapeStatus.PROCESSING
        )

        # 5. (关键!) 触发 Celery 异步任务
        #    我们把新创建的 product.id 传给它
        from .tasks import task_scrape_product
        task_scrape_product.delay(product.id)

        # 6. 返回新创建的 Post 实例
        return post