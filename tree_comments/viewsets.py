from rest_framework import mixins, pagination, permissions, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from tree_comments import get_comment_model, signals

from .serializers import (
    TreeCommentCreateSerializer,
    TreeCommentListWithParentUserSerializer,
    TreeCommentUpdateSerializer,
)

CommentModel = get_comment_model()


class TreeCommentCreateUpdateViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    create_serializer_class = TreeCommentCreateSerializer
    update_serializer_class = TreeCommentUpdateSerializer

    def get_queryset(self):
        return CommentModel.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return self.create_serializer_class
        if self.action in {"update", "partial_update"}:
            return self.update_serializer_class
        return super().get_serializer_class()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        signals.comment_posted.send(
            sender=instance.__class__,
            comment=instance,
            request=self.request,
        )

    def perform_update(self, serializer):
        instance = serializer.save(user=self.request.user)
        signals.comment_edited.send(
            sender=instance.__class__,
            comment=instance,
            request=self.request,
        )


class TreeCommentLimitOffsetPagination(pagination.LimitOffsetPagination):
    default_limit = 50


class TreeCommentListViewSet(
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TreeCommentListWithParentUserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = TreeCommentLimitOffsetPagination

    def get_queryset(self):
        qs = CommentModel.objects.all().select_related("user", "parent", "parent__user").order_by("created_at")
        return self.filter_queryset_by_parents_lookups(qs)
