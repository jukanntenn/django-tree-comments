from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "enable_comments")
    list_filter = ("enable_comments", "author")
    search_fields = ("title", "body")
