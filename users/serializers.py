from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User, UserFollow, MerchantProfile

class UserCreateSerializer(BaseUserCreateSerializer):
    """
    用于"注册"的序列化器
    """
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        # 我们允许用户在注册时只提交这三个字段
        fields = ('id', 'username', 'email', 'password', 'avatar')

class UserSerializer(BaseUserSerializer):
    """
    用于"读取"用户信息的序列化器 (例如 /auth/users/me/)
    """
    class Meta(BaseUserSerializer.Meta):
        model = User
        # 我们只暴露这些"安全"的字段，绝不能暴露 password_hash
        fields = ('id', 'username', 'email', 'avatar',
                  'is_followers_public',
                  'is_following_public',
                  'is_joined_topics_public',
                  'is_created_topics_public'
                  )

class ProfileSerializer(serializers.ModelSerializer):
    """
    用于公开展示的用户个人主页信息
    """
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_followed = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        # 我们只暴露公开字段，绝不要暴露 email 或 password
        fields = ['id', 'username', 'date_joined', 'followers_count', 'following_count', 'is_followed', 'is_blocked', 'avatar']

    def get_is_followed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 检查当前登录用户 (request.user) 是否关注了该用户 (obj)
            # user_follow 表中: follower=我, followed=他
            return UserFollow.objects.filter(follower=request.user, followed=obj).exists()
        return False

    def get_is_blocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # 检查我 (request.user) 是否拉黑了他 (obj)
            from .models import UserBlock  # 局部导入防止循环引用
            return UserBlock.objects.filter(blocker=request.user, blocked=obj).exists()
        return False

class MerchantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantProfile
        # 前端提交: shop_name, description, license_image
        # 后端返回: status, reject_reason
        fields = ['id', 'shop_name', 'description', 'license_image', 'status', 'reject_reason', 'created_at']
        read_only_fields = ['status', 'reject_reason', 'created_at'] # 用户不能自己改状态