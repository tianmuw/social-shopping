from rest_framework.routers import DefaultRouter
from .views import TopicViewSet

# DRF 的 DefaultRouter 会自动为我们的 ViewSet 生成 URL
# 例如：/topics/ (列表) 和 /topics/{slug}/ (详情)
router = DefaultRouter()
router.register(r'topics', TopicViewSet, basename='topic') # 'topics' 是 URL 前缀

# 我们不需要 urlpatterns，因为 router 会帮我们处理
# 但为了 Django 规范，我们写上
urlpatterns = router.urls