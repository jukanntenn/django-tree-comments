import time

from tests.app.models import Post
from tree_comments import get_comment_model
from tree_comments.forms import CommentForm


class TestCommentForm:
    def tamper_with_form(self, post, **kwargs):
        """Helper method to create tampered form data"""
        data = self.get_valid_data(post)
        data.update(kwargs)
        form = CommentForm(target_object=post, data=data)
        assert not form.is_valid()
        return form

    def get_valid_data(self, post, parent=None):
        """Helper method to generate valid form data"""
        form = CommentForm(target_object=post, parent=parent)
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "url": "http://example.com",
            "comment": "This is my comment",
            "content_type": form.initial["content_type"],
            "object_pk": form.initial["object_pk"],
            "timestamp": form.initial["timestamp"],
            "security_hash": form.initial["security_hash"],
            "honeypot": "",
        }
        if parent is not None:
            data["parent"] = str(form.initial["parent"])
        return data

    def test_init(self, post):
        form = CommentForm(target_object=post)

        assert form.initial["content_type"] == str(Post._meta)
        assert form.initial["object_pk"] == str(post.pk)
        assert form.initial["security_hash"] is not None
        assert form.initial["timestamp"] is not None

    def test_valid_post(self, post):
        form = CommentForm(target_object=post, data=self.get_valid_data(post))
        assert form.is_valid(), form.errors

    def test_init_with_parent(self, post, comment):
        form = CommentForm(target_object=post, parent=comment)

        assert form.initial["parent"] == comment.pk

    def test_valid_post_with_parent(self, post, comment):
        form = CommentForm(target_object=post, data=self.get_valid_data(post, parent=comment))
        assert form.is_valid(), form.errors

        new_comment = form.get_comment_object()
        assert new_comment.parent_id == comment.pk

        new_comment.save()
        assert new_comment.parent_id == comment.pk

    def test_honeypot_tampering(self, post):
        self.tamper_with_form(post, honeypot="I am a robot")

    def test_timestamp_tampering(self, post):
        self.tamper_with_form(post, timestamp=str(time.time() - 28800))

    def test_security_hash_tampering(self, post):
        self.tamper_with_form(post, security_hash="Nobody expects the Spanish Inquisition!")

    def test_content_type_tampering(self, post):
        self.tamper_with_form(post, content_type="auth.user")

    def test_object_pk_tampering(self, post):
        self.tamper_with_form(post, object_pk="999")

    def test_parent_tampering(self, post):
        form = self.tamper_with_form(post, parent="999999")
        assert "parent" in form.errors
        assert "does not exist" in form.errors["parent"][0]

    def test_empty_parent_is_valid(self, post):
        data = self.get_valid_data(post)
        data["parent"] = ""
        form = CommentForm(target_object=post, data=data)
        assert form.is_valid(), form.errors

        new_comment = form.get_comment_object()
        assert new_comment.parent_id is None

    def test_security_errors(self, post):
        form = self.tamper_with_form(post, honeypot="I am a robot")
        assert "honeypot" in form.security_errors()

    def test_get_comment_object(self, post):
        form = CommentForm(target_object=post, data=self.get_valid_data(post))
        assert form.is_valid(), form.errors

        comment = form.get_comment_object()
        Comment = get_comment_model()
        assert isinstance(comment, Comment)
        assert comment.content_object == post
        assert comment.comment == "This is my comment"

        # Save and verify count
        comment.save()
        assert Comment.objects.count() == 1

    def test_get_comment_object_with_site(self, post, site):
        data = self.get_valid_data(post)
        data["comment"] = "testGetCommentObject with a site"
        form = CommentForm(target_object=post, data=data)
        assert form.is_valid(), form.errors

        comment = form.get_comment_object(site_id=site.id)
        assert comment.site_id == site.id
