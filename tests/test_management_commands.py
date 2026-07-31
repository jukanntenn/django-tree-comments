import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import call_command

from tests.app.models import Post
from tree_comments.models import Comment

User = get_user_model()


@pytest.mark.django_db
class TestManagementCommands:
    def setup_method(self):
        site = Site.objects.get_current()
        user = User.objects.create_user(username="alice")
        post = Post.objects.create(title="test post", author=user)

        user_ctype = ContentType.objects.get_for_model(User)
        post_ctype = ContentType.objects.get_for_model(Post)

        self.post = post

        self.c1 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 2",
            is_public=False,
            is_removed=False,
        )

        self.c2 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 3",
            is_public=True,
            is_removed=False,
        )

        self.c3 = Comment.objects.create(
            content_type=user_ctype,
            object_pk=user.pk,
            site=site,
            user=user,
            comment="test comment 4",
            is_public=False,
            is_removed=False,
        )

    def test_does_not_remove_when_no_stale_comments(self):
        """Test that delete_stale_comments doesn't remove comments when parent objects exist."""
        initial_count = Comment.objects.count()

        call_command("delete_stale_comments", "--yes", verbosity=0)

        assert initial_count == Comment.objects.count()

    def test_removes_when_parent_objects_are_missing(self):
        """Test that delete_stale_comments removes comments when parent objects are missing."""
        initial_count = Comment.objects.count()
        post_comments_count = Comment.objects.for_model(Post).count()
        assert post_comments_count > 0

        # Removing posts will not remove associated comments
        Post.objects.all().delete()
        assert initial_count == Comment.objects.count()

        call_command("delete_stale_comments", "--yes", verbosity=0)

        assert Comment.objects.for_model(Post).count() == 0
        assert (initial_count - post_comments_count) == Comment.objects.count()
