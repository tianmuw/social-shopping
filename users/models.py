from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    # 我们继承 AbstractUser，它自带了 username, email, password 等字段

    # 以后我们可以很方便地在这里添加新字段
    # profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.username
