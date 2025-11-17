from django.contrib import admin
from .models import Topic

class TopicAdmin(admin.ModelAdmin):
    # 让 slug 自动根据 name 填充
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'slug', 'description')

admin.site.register(Topic, TopicAdmin)