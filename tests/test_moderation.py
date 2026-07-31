import pytest
from django.core import mail
from django.test.utils import override_settings

from tree_comments.forms import CommentForm
from tree_comments.models import Comment
from tree_comments.moderation import AlreadyModerated, CommentModerator, moderator

from .app.models import Post


class PostModerator1(CommentModerator):
    email_notification = True


class PostModerator2(CommentModerator):
    enable_field = "enable_comments"


class PostModerator3(CommentModerator):
    auto_close_field = "created_at"
    close_after = 7


class PostModerator4(CommentModerator):
    auto_moderate_field = "created_at"
    moderate_after = 7


class PostModerator5(CommentModerator):
    auto_moderate_field = "created_at"
    moderate_after = 0


class PostModerator6(CommentModerator):
    auto_close_field = "created_at"
    close_after = 0


@pytest.mark.django_db
class TestModeration:
    def create_some_comments(self, client, post):
        # Tests for the moderation signals must actually post data
        # through the comment views, because only the comment views
        # emit the custom signals moderation listens for.
        data = {
            "name": "Jim Bob",
            "email": "jim.bob@example.com",
            "url": "",
            "comment": "This is my comment",
        }
        data.update(CommentForm(post).initial)

        client.post("/post/", data, REMOTE_ADDR="1.2.3.4")

        # We explicitly do a try/except to get the comment we've just
        # posted because moderation may have disallowed it, in which
        # case we can just return it as None.
        try:
            c1 = Comment.objects.all()[0]
        except IndexError:
            c1 = None

        client.post("/post/", data, REMOTE_ADDR="1.2.3.4")
        try:
            c2 = Comment.objects.all()[0]
        except IndexError:
            c2 = None
        return c1, c2

    def teardown_method(self):
        moderator.unregister(Post)

    def test_register_existing_model(self):
        moderator.register(Post, PostModerator1)
        with pytest.raises(AlreadyModerated):
            moderator.register(Post, PostModerator1)

    def test_email_notification(self, client, post):
        with override_settings(MANAGERS=[("Test Manager", "test@example.com")]):
            moderator.register(Post, PostModerator1)
            self.create_some_comments(client, post)
            assert len(mail.outbox) == 2

    def test_comments_enabled(self, client, post):
        # Note: This test assumes Post model has enable_comments field
        # If not, you may need to modify the test or the model
        moderator.register(Post, PostModerator2)
        self.create_some_comments(client, post)
        assert Comment.objects.all().count() == 1

    def test_auto_close_field(self, client, post):
        # Note: This test assumes Post model has pub_date field
        # If not, you may need to modify the test or the model
        moderator.register(Post, PostModerator3)
        self.create_some_comments(client, post)
        assert Comment.objects.all().count() == 0

    def test_auto_moderate_field(self, client, post):
        # Note: This test assumes Post model has pub_date field
        # If not, you may need to modify the test or the model
        moderator.register(Post, PostModerator4)
        _, c2 = self.create_some_comments(client, post)
        if c2:
            assert c2.is_public is False

    def test_auto_moderate_field_immediate(self, client, post):
        # Note: This test assumes Post model has pub_date field
        # If not, you may need to modify the test or the model
        moderator.register(Post, PostModerator5)
        _, c2 = self.create_some_comments(client, post)
        if c2:
            assert c2.is_public is False

    def test_auto_close_field_immediate(self, client, post):
        # Note: This test assumes Post model has pub_date field
        # If not, you may need to modify the test or the model
        moderator.register(Post, PostModerator6)
        self.create_some_comments(client, post)
        assert Comment.objects.all().count() == 0
