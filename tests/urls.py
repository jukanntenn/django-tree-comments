from django.urls import include, path

from tree_comments.feeds import LatestCommentFeed

feeds = {
    "comments": LatestCommentFeed,
}

urlpatterns = [
    path("", include("tree_comments.urls")),
    path("rss/comments/", LatestCommentFeed()),
]
