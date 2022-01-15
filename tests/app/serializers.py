from django.contrib.auth.models import User
from rest_framework import serializers

from tree_comments.serializers import TreeCommentCreateSerializer


class CommentCreateSerializer(TreeCommentCreateSerializer):
    class Meta(TreeCommentCreateSerializer.Meta):
        fields = TreeCommentCreateSerializer.Meta.fields + ["post"]


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]
