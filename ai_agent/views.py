# backend/ai_agent/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from pgvector.django import CosineDistance

# LangChain & 阿里云 相关
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.llms import Tongyi
from langchain_core.messages import HumanMessage, SystemMessage

from posts.models import Post
from posts.serializers import PostListRetrieveSerializer  # 复用现有的序列化器来返回商品卡片

import os
from dotenv import load_dotenv
load_dotenv()
DASHSCOPE_API_KEY=os.environ["DASHSCOPE_API_KEY"]

class AIChatView(APIView):
    """
    AI 导购对话接口
    POST /api/v1/ai/chat/
    Body: { "query": "我想买个耳机" }
    """
    # 允许登录用户使用 (甚至可以允许匿名，看你需求)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({'detail': '请输入问题'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. 将用户问题转换为向量 (Embedding)
            embeddings = DashScopeEmbeddings(model="text-embedding-v1")
            query_vec = embeddings.embed_query(query)

            # 2. 向量搜索：在数据库中寻找最相似的 5 个帖子
            # 使用 CosineDistance (余弦距离) 进行排序，距离越小越相似
            related_posts = Post.objects.order_by(
                CosineDistance('embedding', query_vec)
            )[:5]

            # 3. 构建给大模型 (LLM) 的上下文 (Context)
            context_text = ""
            for post in related_posts:
                # 我们把帖子的标题、内容、价格(如果有)都告诉 AI
                price = post.product.product_price if hasattr(post, 'product') else "未知"
                context_text += f"--- 商品/帖子 ID: {post.id} ---\n"
                context_text += f"标题: {post.title}\n"
                context_text += f"内容摘要: {post.content[:200]}...\n"  # 截取前200字防止 token 超限
                context_text += f"价格: {price}\n\n"

            # 4. 构建 Prompt (提示词)
            system_prompt = """你是一个专业的电商导购助手 SocialShop AI。
            你的任务是根据用户的问题，结合下面提供的[参考商品信息]，为用户提供购买建议。

            要求：
            1. 语气亲切、专业、有帮助。
            2. 必须基于[参考商品信息]来推荐，不要编造不存在的商品。
            3. 如果参考信息里有合适的，请具体提到商品标题。
            4. 如果参考信息里没有相关的，请礼貌告知用户暂时没找到，并给出一些通用的选购建议。
            """

            user_prompt = f"""
            [参考商品信息]:
            {context_text}

            [用户问题]:
            {query}

            请回答：
            """

            # 5. 调用通义千问大模型 (Qwen) 生成回答
            llm = Tongyi()  # 使用速度较快的 turbo 模型，或者 plus
            ai_response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # 获取文本内容 (兼容不同版本的 LangChain 返回格式)
            answer_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)

            # 6. 返回结果
            # 我们不仅返回 AI 的话，还把那 5 个相关的帖子完整数据返回去，
            # 这样前端就可以直接渲染 5 个 PostCard 卡片！
            serializer = PostListRetrieveSerializer(related_posts, many=True, context={'request': request})

            return Response({
                'answer': answer_text,
                'recommendations': serializer.data
            })

        except Exception as e:
            print(f"AI Error: {e}")
            return Response({'detail': 'AI 暂时繁忙，请稍后再试。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)