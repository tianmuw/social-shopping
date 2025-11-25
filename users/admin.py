# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserFollow, UserBlock, MerchantProfile

# 1. 注册 User 模型
# 使用 UserAdmin 可以保留 Django 自带的强大的用户管理功能 (如修改密码表单、权限管理等)
admin.site.register(User, UserAdmin)

# 2. 注册 MerchantProfile (商家档案) - 你刚才添加的
@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('shop_name', 'user__username')
    actions = ['approve_merchant', 'reject_merchant']

    def approve_merchant(self, request, queryset):
        queryset.update(status='approved')
    approve_merchant.short_description = "通过审核"

    def reject_merchant(self, request, queryset):
        queryset.update(status='rejected')
    reject_merchant.short_description = "拒绝申请"

# 3. 注册 UserFollow (关注关系) - 新增
@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    # 这样你就能在后台列表中直接看到是谁关注了谁
    list_display = ('follower', 'followed', 'created_at')
    # 支持按用户名搜索
    search_fields = ('follower__username', 'followed__username')
    list_filter = ('created_at',)

# 4. 注册 UserBlock (拉黑关系) - 新增
@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
    list_filter = ('created_at',)