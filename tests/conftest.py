from datetime import timedelta

import pytest
from django.contrib.sites.models import Site
from django.utils import timezone

from tests.factories import CommentFactory, PostFactory


@pytest.fixture
def site():
    return Site.objects.get_current()


@pytest.fixture
def post(admin_user):
    return PostFactory(
        title="test post",
        author=admin_user,
        enable_comments=True,
        created_at=timezone.now() - timedelta(days=30),
    )


@pytest.fixture
def comment(site, post, admin_user):
    return CommentFactory(
        target_object=post,
        site=site,
        user=admin_user,
        comment="test comment",
    )


@pytest.fixture
def anonymous_comment(site, post):
    return CommentFactory(
        target_object=post,
        site=site,
        user=None,
        user_name="anonymous",
        user_email="anonymous@example.com",
        user_url="https://example.com",
        comment="anonymous comment",
    )
