from django.db import models
from django.conf import settings
from django.utils.text import slugify
from xpinyin import Pinyin


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="话题名称")
    # "slug" 是一个用于 URL 的友好字符串，例如 "华山旅游" -> "huashan-travel"
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name="URL Slug")
    description = models.TextField(max_length=500, blank=True, verbose_name="话题描述")
    # topic_image = models.ImageField(upload_to='topics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    icon = models.ImageField(upload_to='topics/', blank=True, null=True, verbose_name="话题图标")

    banner = models.ImageField(upload_to='topics/banners/', blank=True, null=True, verbose_name="话题背景图")

    # 记录话题创建者
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 如果用户注销，话题保留，但在显示时显示为"已注销用户"
        null=True,
        blank=True,
        related_name="created_topics",
        verbose_name="创建者"
    )

    # 修改：我们不需要在这里直接定义 subscribers ManyToMany
    # 因为我们下面会创建一个中间模型 TopicSubscription 来管理它，这样更灵活

    def save(self, *args, **kwargs):
        # 自动根据 name 生成 slug
        if not self.slug:
            p = Pinyin()
            self.slug = p.get_pinyin(self.name, '-')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TopicSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_subscriptions")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'topic') # 确保用户不能重复加入同一个话题

    def __str__(self):
        return f"{self.user} joined {self.topic}"