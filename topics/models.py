from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="话题名称")
    # "slug" 是一个用于 URL 的友好字符串，例如 "华山旅游" -> "huashan-travel"
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name="URL Slug")
    description = models.TextField(max_length=500, blank=True, verbose_name="话题描述")
    # topic_image = models.ImageField(upload_to='topics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 关注者 (一个话题可以被多个用户关注)
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="subscribed_topics", blank=True)

    def save(self, *args, **kwargs):
        # 自动根据 name 生成 slug
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name