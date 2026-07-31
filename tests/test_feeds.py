from xml.etree import ElementTree as ET

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from tree_comments.models import Comment


@pytest.mark.django_db
class TestFeeds:
    feed_url = "/rss/comments/"

    def test_feed(self, client, post):
        """Test RSS feed generation and content."""

        site_2 = Site.objects.create(id=settings.SITE_ID + 1, domain="example2.com", name="example2.com")
        # A comment for another site
        Comment.objects.create(
            content_type=ContentType.objects.get_for_model(post),
            object_pk=post.pk,
            user_name="Joe Somebody",
            user_email="jsomebody@example.com",
            user_url="http://example.com/~joe/",
            comment="A comment for the second site.",
            site=site_2,
        )
        response = client.get(self.feed_url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/rss+xml; charset=utf-8"

        rss_elem = ET.fromstring(response.content)

        assert rss_elem.tag == "rss"
        assert rss_elem.attrib == {"version": "2.0"}

        channel_elem = rss_elem.find("channel")

        title_elem = channel_elem.find("title")
        assert title_elem.text == "example.com comments"

        link_elem = channel_elem.find("link")
        assert link_elem.text == "http://example.com/"

        atomlink_elem = channel_elem.find("{http://www.w3.org/2005/Atom}link")
        assert atomlink_elem.attrib == {
            "href": "http://example.com/rss/comments/",
            "rel": "self",
        }

        assert "A comment for the second site." not in response.content.decode()
