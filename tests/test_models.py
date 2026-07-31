import pytest
from django.contrib.contenttypes.models import ContentType

from tests.app.models import Post


@pytest.mark.django_db
class TestComment:
    def test___str__(self, comment):
        assert str(comment) == "admin: test comment..."

        comment.comment = "a" * 100
        truncated = "a" * 50
        assert str(comment) == f"admin: {truncated}..."

    def test_save(self, comment):
        assert comment.submit_date is not None

    def test_userinfo_property_anonymous(self, anonymous_comment):
        assert anonymous_comment.userinfo == {
            "name": "anonymous",
            "email": "anonymous@example.com",
            "url": "https://example.com",
        }

    def test_userinfo_property_authenticated(self, comment):
        assert comment.userinfo == {
            "name": "admin",
            "email": "admin@example.com",
            "url": "",
        }

    def test_name_property_read_only(self, comment):
        with pytest.raises(
            AttributeError,
            match="This comment was posted by an authenticated user and thus the name is read-only.",
        ):
            comment.name = "other user"

    def test_email_property_read_only(self, comment):
        with pytest.raises(
            AttributeError,
            match="This comment was posted by an authenticated user and thus the email is read-only.",
        ):
            comment.email = "other@example.com"

    def test_as_text(self, comment):
        post_ct = ContentType.objects.get_for_model(Post)
        post_pk = comment.content_object.pk
        assert (
            comment.get_as_text()
            == f"Posted by admin at {comment.submit_date}\n\n{comment.comment}\n\nhttp://example.com/cr/{post_ct.pk}/{post_pk}/#c{comment.pk}"
        )

    def test_get_content_object_url(self, comment):
        post_ct = ContentType.objects.get_for_model(Post)
        post_pk = comment.content_object.pk
        assert comment.get_content_object_url() == f"/cr/{post_ct.pk}/{post_pk}/"
