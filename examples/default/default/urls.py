from blog.views import htmx_delete_comment
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("blog.urls")),
    path("comments/", include("tree_comments.urls")),
    path(
        "htmx/comments/<int:comment_id>/delete/",
        htmx_delete_comment,
        name="htmx-delete-comment",
    ),
]
