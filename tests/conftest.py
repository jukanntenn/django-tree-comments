from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils import timezone

from tests.app.models import Article, Post
from tree_comments.models import Comment


@pytest.fixture
def site():
    return Site.objects.get_current()


@pytest.fixture
def post(admin_user):
    return Post.objects.create(
        title="test post",
        author=admin_user,
        enable_comments=True,
        created_at=timezone.now() - timedelta(days=30),
    )


@pytest.fixture
def comment(site, post, admin_user):
    return Comment.objects.create(
        content_type=ContentType.objects.get_for_model(Post),
        object_pk=post.pk,
        site=site,
        user=admin_user,
        comment="test comment",
    )


@pytest.fixture
def anonymous_comment(site, post):
    return Comment.objects.create(
        content_type=ContentType.objects.get_for_model(Post),
        object_pk=post.pk,
        site=site,
        user_name="anonymous",
        user_email="anonymous@example.com",
        user_url="https://example.com",
        comment="anonymous comment",
    )


@pytest.fixture
def article(db):
    """Create a test article for comments."""
    return Article.objects.create(title="Test Article")
