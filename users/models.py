from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


# Create your models here.
class User(AbstractUser):
    # 我们继承 AbstractUser，它自带了 username, email, password 等字段

    # 以后我们可以很方便地在这里添加新字段
    # profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.username


class UserFollow(models.Model):
    # "follower" 是谁在关注 (比如我)
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")

    # "followed" 是被关注的人 (比如 Mike)
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # 确保不能重复关注
        # 可选：防止自己关注自己 (可以在 View 中校验)

    def __str__(self):
        return f"{self.follower} follows {self.followed}"