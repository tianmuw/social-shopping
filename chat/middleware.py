# backend/chat/middleware.py
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        # 验证 Token
        UntypedToken(token_key)
        # 解码 Token 获取 User ID
        decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_data['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # 从 query string 获取 token
        # scope['query_string'] 是 bytes 类型，例如 b'token=EyJ...'
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            scope['user'] = await get_user(token)

        # 如果没有 token，scope['user'] 默认为 AnonymousUser (或者由 SessionMiddleware 填充)
        # 但为了优先使用 JWT，我们在这里覆盖它

        return await super().__call__(scope, receive, send)