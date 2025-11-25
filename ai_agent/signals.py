# backend/ai_agent/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from posts.models import Post
from .tasks import generate_post_embedding
from django.db import transaction


@receiver(post_save, sender=Post)
def trigger_embedding_generation(sender, instance, created, **kwargs):
    """
    监听 Post 模型的保存事件。
    如果是新创建的，或者内容被修改了（这里简化为每次保存都触发），
    就丢给 Celery 去生成向量。
    """
    # 1. 获取本次保存更新了哪些字段
    update_fields = kwargs.get('update_fields')

    # 2. 核心判断：如果是任务自己在更新 embedding，直接退出，打断循环
    # 我们在 tasks.py 里写的是 post.save(update_fields=['embedding'])
    if update_fields and 'embedding' in update_fields and len(update_fields) == 1:
        return

    # 3. 正常触发：如果是创建新帖，或者修改了其他内容
    transaction.on_commit(lambda: generate_post_embedding.delay(instance.id))