from django.conf import settings
from django.db import models
from django.utils import timezone

from tree_comments.models import AbstractTreeComment


class Post(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="user",
        related_name="posts",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "post"
        verbose_name_plural = "posts"

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)


class SimpleComment(AbstractTreeComment):
    class Meta:
        verbose_name = "simple_comment"
        verbose_name_plural = "simple_comments"


class Comment(AbstractTreeComment):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = "comments"
