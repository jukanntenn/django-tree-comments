from django.contrib.contenttypes.views import shortcut
from django.urls import path, re_path

from .views import (
    ApproveDoneView,
    ApproveView,
    CommentDoneView,
    CommentFormTemplateView,
    CommentPostView,
    DeleteDoneView,
    DeleteView,
    FlagDoneView,
    FlagView,
    ReplyView,
)

urlpatterns = [
    re_path(r"^cr/(\d+)/(.+)/$", shortcut, name="tree-comments-url-redirect"),
    path("post/", CommentPostView.as_view(), name="tree-comments-post-comment"),
    path("posted/", CommentDoneView.as_view(), name="tree-comments-comment-done"),
    path("flag/<int:comment_id>/", FlagView.as_view(), name="tree-comments-flag"),
    path("flagged/", FlagDoneView.as_view(), name="tree-comments-flag-done"),
    path("delete/<int:comment_id>/", DeleteView.as_view(), name="tree-comments-delete"),
    path("deleted/", DeleteDoneView.as_view(), name="tree-comments-delete-done"),
    path(
        "approve/<int:comment_id>/",
        ApproveView.as_view(),
        name="tree-comments-approve",
    ),
    path("approved/", ApproveDoneView.as_view(), name="tree-comments-approve-done"),
    path("form/", CommentFormTemplateView.as_view(), name="tree-comments-form"),
    path("<int:comment_id>/reply/", ReplyView.as_view(), name="tree-comments-reply"),
]
