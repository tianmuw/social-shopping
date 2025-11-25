# backend/ai_agent/tasks.py
from celery import shared_task
from langchain_community.embeddings import DashScopeEmbeddings
from posts.models import Post
import os
from django.conf import settings


@shared_task
def generate_post_embedding(post_id):
    """
    Celery 异步任务：为帖子生成语义向量 (Embedding)
    """
    try:
        # 1. 获取帖子对象
        post = Post.objects.get(id=post_id)
        print(f"🤖 AI Agent: 开始处理帖子 {post.title} (ID: {post.id})...")

        # 2. 准备要向量化的文本
        # 我们把标题和内容拼接起来，这样搜索时既能搜标题也能搜内容
        text_to_embed = f"{post.title}\n{post.content}"

        # 3. 初始化阿里云通义千问 Embedding 模型
        # 它会自动读取环境变量 DASHSCOPE_API_KEY
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",  # 阿里云推荐的通用文本向量模型
        )

        # 4. 调用 API 生成向量 (这是一个耗时网络请求)
        # 返回的是一个包含 1536 个浮点数的列表
        vector = embeddings.embed_query(text_to_embed)

        # 5. 保存回数据库
        post.embedding = vector
        post.save(update_fields=['embedding'])  # 只更新 embedding 字段，避免覆盖其他并发修改

        return f"✅ Success: Generated embedding for Post {post_id}"

    except Post.DoesNotExist:
        return f"❌ Error: Post {post_id} not found"
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return f"Error generating embedding: {str(e)}"