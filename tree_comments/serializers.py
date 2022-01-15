from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from rest_framework import serializers

from tree_comments import get_comment_model

CommentModel = get_comment_model()
UserModel = get_user_model()


class TreeCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentModel
        fields = [
            "id",
            "parent",
            "content",
            "created_at",
        ]
        read_only_fields = [
            "created_at",
        ]


class TreeCommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentModel
        fields = [
            "id",
            "content",
        ]


class DefaultUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            "username",
        ]


if getattr(settings, "TREE_COMMENTS_USER_SERIALIZER", None):
    UserSerializer = import_string(settings.TREE_COMMENTS_USER_SERIALIZER)
else:
    UserSerializer = DefaultUserSerializer


class TreeCommentListWithParentUserSerializer(serializers.ModelSerializer):
    parent_user = UserSerializer(source="parent.user", default=None)
    user = UserSerializer()

    class Meta:
        model = CommentModel
        fields = [
            "id",
            "content",
            "created_at",
            "user",
            "parent_user",
        ]
