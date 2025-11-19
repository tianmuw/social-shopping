from rest_framework import serializers
from .models import Post, AssociatedProduct, Comment, Vote
from users.models import User
from topics.models import Topic
from posts.models import Vote
from django.db.models import Sum

# 我们需要创建几个"微型"的只读序列化器，用于嵌套

class PostUserSerializer(serializers.ModelSerializer):
    """用于 Post 作者的"微型"序列化器"""

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class PostTopicSerializer(serializers.ModelSerializer):
    """用于 Post 话题的"微型"序列化器"""

    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug', 'icon']


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

    # (!!!) 新增下面两个字段 (!!!)
    score = serializers.IntegerField(read_only=True)  # 将由 annotation (注解) 提供
    user_vote = serializers.SerializerMethodField()  # 需要我们手动计算

    comments_count = serializers.IntegerField(read_only=True)

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
            'score',  # <-- (!!!) 添加到 fields
            'user_vote',  # <-- (!!!) 添加到 fields
            'comments_count',
        ]

    def get_user_vote(self, obj):
        # 从 context 中获取 request 对象
        request = self.context.get('request', None)
        if not request or not request.user.is_authenticated:
            return None

        user = request.user

        # 这是一个高性能的查询，因为它使用了我们下一步
        # 就会在 viewset 中添加的 'prefetch_related'
        # 它会在内存中查找，而不是去查数据库
        for vote in obj.votes.all():
            if vote.user_id == user.id:
                return vote.vote_type

        return None

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

class VoteSerializer(serializers.ModelSerializer):
    """
    用于验证投票的序列化器
    """
    # 我们用 ChoiceField 来确保 vote_type 只能是 1 或 -1
    vote_type = serializers.ChoiceField(choices=Vote.VoteType.choices)

    class Meta:
        model = Vote
        fields = ['vote_type']


# posts/serializers.py (在文件底部追加)

class RecursiveCommentSerializer(serializers.Serializer):
    """
    一个辅助的、只读的、递归的序列化器。
    它告诉 Django: "如何显示一个'回复' (reply)"
    """

    def to_representation(self, value):
        # 我们在这里"手动"调用父序列化器 (CommentSerializer)
        # 这就实现了无限层级的递归
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CommentSerializer(serializers.ModelSerializer):
    """
    用于"读取"和"创建"评论的主序列化器
    """
    # "读" (Read) 字段
    author = PostUserSerializer(read_only=True)  # 嵌套显示作者

    # (关键) 嵌套显示"回复"
    # many=True 告诉它'replies'是一个列表
    # read_only=True 告诉它这个字段只用于"读"，不用于"写"
    replies = RecursiveCommentSerializer(many=True, read_only=True)

    # "写" (Write) 字段
    # 我们需要一个'parent'字段，但它只在"创建"时使用
    # 'pk' (Primary Key) 允许我们只发送一个 ID，比如 { "parent": 10 }
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        write_only=True,  # 只"写"不"读"
        allow_null=True  # 允许为 null (即这是一个顶级评论)
    )

    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'author',  # (只读)
            'created_at',  # (只读)
            'replies',  # (只读 - 用于'盖楼')
            'parent',  # (只写 - 用于回复)
        ]

        # (新) 我们告诉 DRF，'parent' 字段不是必需的
        # 如果不提供 'parent'，它就是顶级评论
        extra_kwargs = {
            'parent': {'required': False}
        }