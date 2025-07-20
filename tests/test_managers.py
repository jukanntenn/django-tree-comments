import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from tests.app.models import Post
from tree_comments.models import Comment

User = get_user_model()


@pytest.mark.django_db
class TestManager:
    def setup_method(self):
        site = Site.objects.get_current()
        user = User.objects.create_user(username="alice")
        post = Post.objects.create(title="test post", author=user)

        user_ctype = ContentType.objects.get_for_model(User)
        post_ctype = ContentType.objects.get_for_model(Post)

        self.post = post

        self.c1 = Comment.objects.create(
            content_type=user_ctype,
            object_pk=user.pk,
            site=site,
            user=user,
            comment="test comment 1",
            is_public=True,
            is_removed=True,
        )

        self.c2 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 2",
            is_public=False,
            is_removed=False,
        )

        self.c3 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 3",
            is_public=True,
            is_removed=False,
        )

        self.c4 = Comment.objects.create(
            content_type=user_ctype,
            object_pk=user.pk,
            site=site,
            user=user,
            comment="test comment 4",
            is_public=False,
            is_removed=False,
        )

        self.c5 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 5",
            is_public=True,
            is_removed=False,
            parent=self.c3,
        )

        self.c6 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            comment="test comment 6",
            is_public=True,
            is_removed=False,
        )

    def test_in_moderation(self):
        moderated_comments = list(Comment.objects.in_moderation().order_by("id"))
        assert moderated_comments == [self.c2, self.c4]

    def test_for_model(self):
        post_comments = list(Comment.objects.for_model(self.post).order_by("id"))
        user_comments = list(Comment.objects.for_model(self.c1.user))
        assert post_comments == [self.c2, self.c3, self.c5, self.c6]
        assert user_comments == [self.c1, self.c4]

    def test_visible(self):
        visible_comments = list(Comment.objects.visible().order_by("id"))
        assert visible_comments == [self.c3, self.c5, self.c6]

    def test_roots(self):
        root_comments = list(Comment.objects.roots().order_by("id"))
        assert root_comments == [self.c3, self.c6]

    def test_threaded_for_instance(self):
        # Add more children to build a richer tree under the same post
        c6_child1 = Comment.objects.create(
            content_type=self.c6.content_type,
            object_pk=self.c6.object_pk,
            site=self.c6.site,
            user=self.c6.user,
            comment="c6 child 1",
            is_public=True,
            is_removed=False,
            parent=self.c6,
        )

        c6_child2 = Comment.objects.create(
            content_type=self.c6.content_type,
            object_pk=self.c6.object_pk,
            site=self.c6.site,
            user=self.c6.user,
            comment="c6 child 2",
            is_public=True,
            is_removed=False,
            parent=self.c6,
        )

        c6_child3 = Comment.objects.create(
            content_type=self.c6.content_type,
            object_pk=self.c6.object_pk,
            site=self.c6.site,
            user=self.c6.user,
            comment="c6 child 3",
            is_public=True,
            is_removed=False,
            parent=self.c6,
        )

        c3_child2 = Comment.objects.create(
            content_type=self.c3.content_type,
            object_pk=self.c3.object_pk,
            site=self.c3.site,
            user=self.c3.user,
            comment="c3 child 2",
            is_public=True,
            is_removed=False,
            parent=self.c3,
        )

        threaded = list(Comment.objects.threaded_for_instance(self.post))

        # Expect order grouped by root (desc root_id), then by submit_date, then id
        expected = [
            self.c6,
            c6_child1,
            c6_child2,
            c6_child3,
            self.c3,
            self.c5,
            c3_child2,
        ]

        assert threaded == expected

        # Validate annotations depth and root_id
        actual_meta = [(c.root_id, c.depth) for c in threaded]
        expected_meta = [
            (self.c6.id, 0),
            (self.c6.id, 1),
            (self.c6.id, 1),
            (self.c6.id, 1),
            (self.c3.id, 0),
            (self.c3.id, 1),
            (self.c3.id, 1),
        ]
        assert actual_meta == expected_meta
