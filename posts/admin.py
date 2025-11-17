from django.contrib import admin
from .models import Post, AssociatedProduct, Comment, Vote

admin.site.register(Post)
admin.site.register(AssociatedProduct)
admin.site.register(Comment)
admin.site.register(Vote)