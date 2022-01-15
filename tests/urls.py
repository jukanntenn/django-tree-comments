from rest_framework_extensions.routers import ExtendedSimpleRouter

from tests.app.views import (
    CommentCreateUpdateViewSet,
    CommentListNestedViewSet,
    PostViewSet,
)

router = ExtendedSimpleRouter()
router.register("comments", CommentCreateUpdateViewSet, basename="comment")
posts_router = router.register("posts", PostViewSet, basename="post")
posts_router.register(
    "comments",
    CommentListNestedViewSet,
    basename="posts-comment",
    parents_query_lookups=["post_id"],
)

urlpatterns = router.get_urls()
