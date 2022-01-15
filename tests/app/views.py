from rest_framework import mixins, viewsets

from tree_comments.viewsets import (
    TreeCommentCreateUpdateViewSet,
    TreeCommentListViewSet,
)

from .models import Post
from .serializers import CommentCreateSerializer


class CommentCreateUpdateViewSet(TreeCommentCreateUpdateViewSet):
    create_serializer_class = CommentCreateSerializer


class CommentListNestedViewSet(TreeCommentListViewSet):
    ...


class PostViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return Post.objects.all().order_by("-created_at")
