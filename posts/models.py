from django.db import models
from django.conf import settings

# 导入我们刚创建的 Topic 模型
from topics.models import Topic


class Post(models.Model):
    """
    帖子模型
    """
    title = models.CharField(max_length=255, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    # 帖子和用户是多对一关系 (一个用户可以发多个帖子)
    # on_delete=models.CASCADE 表示用户被删除时，他的帖子也一起被删除
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    # 帖子和话题是多对一关系
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="posts")

    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class AssociatedProduct(models.Model):
    """
    帖子关联的商品
    """

    class ScrapeStatus(models.TextChoices):
        PROCESSING = 'PROCESSING', '处理中'
        SUCCESS = 'SUCCESS', '成功'
        FAILED = 'FAILED', '失败'

    # 商品和帖子是一对一关系 (一个帖子只关联一个商品)
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="product")
    original_url = models.URLField(max_length=1024, verbose_name="原始商品链接")

    # 自动抓取的信息
    product_title = models.CharField(max_length=512, blank=True, null=True, verbose_name="商品标题")
    product_image_url = models.URLField(max_length=1024, blank=True, null=True, verbose_name="商品图片")
    product_price = models.CharField(max_length=100, blank=True, null=True, verbose_name="商品价格")

    scrape_status = models.CharField(
        max_length=20,
        choices=ScrapeStatus.choices,
        default=ScrapeStatus.PROCESSING,
        verbose_name="抓取状态"
    )

    def __str__(self):
        return f"商品: {self.product_title or self.original_url}"


class Comment(models.Model):
    """
    评论模型
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # 盖楼/线程化评论
    # 一个评论可以回复另一个评论，所以和自己建立一个 "多对一" 关系
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    def __str__(self):
        return f"{self.author} 在《{self.post.title}》下的评论"


class Vote(models.Model):
    """
    "顶" / "踩" (投票) 模型
    """

    class VoteType(models.IntegerChoices):
        UPVOTE = 1, '顶'
        DOWNVOTE = -1, '踩'

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes")
    vote_type = models.SmallIntegerField(choices=VoteType.choices)

    class Meta:
        # 确保一个用户对一个帖子只能投一次票
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user} {self.get_vote_type_display()} {self.post.title}"