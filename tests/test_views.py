import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from tests.app.models import Post
from tree_comments import get_comment_flag_model, get_comment_model, signals
from tree_comments.forms import CommentForm
from tree_comments.models import COMMENT_MAX_LENGTH, Comment


@pytest.mark.django_db
class TestCommentViews:
    def get_valid_data(self, obj):
        d = {
            "name": "Jim Bob",
            "email": "jim.bob@example.com",
            "url": "",
            "comment": "This is my comment",
            **CommentForm(obj).initial,
        }
        return d

    def test_post_comment_http_methods(self, client, post):
        data = self.get_valid_data(post)
        response = client.get("/post/", data)
        assert response.status_code == 405
        assert response["Allow"] == "POST"

    def test_post_comment_missing_ctype(self, client, post):
        data = self.get_valid_data(post)
        del data["content_type"]
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_comment_bad_ctype(self, client, post):
        data = self.get_valid_data(post)
        data["content_type"] = "Nobody expects the Spanish Inquisition!"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_comment_bad_ctype_invalid_model_name(self, client, post):
        data = self.get_valid_data(post)
        data["content_type"] = str(Post._meta) + "_91232"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_comment_bad_ctype_injection_attempt(self, client, post):
        data = self.get_valid_data(post)
        data["content_type"] = str(Post._meta) + "'\"()&%<acx><ScRiPt >prompt(998230)</ScRiPt>"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_comment_missing_object_pk(self, client, post):
        data = self.get_valid_data(post)
        del data["object_pk"]
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_comment_bad_object_pk(self, client, post):
        data = self.get_valid_data(post)
        data["object_pk"] = "14"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_invalid_integer_pk(self, client, post):
        data = self.get_valid_data(post)
        data["comment"] = "This is another comment"
        data["object_pk"] = "\ufffd"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_invalid_decimal_pk(self, client, post):
        # Note: This test would need a Book model with decimal PK
        # For now, we'll adapt it to use Post
        data = self.get_valid_data(post)
        data["comment"] = "This is another comment"
        data["object_pk"] = "cookies"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_post_too_long_comment(self, client, post):
        data = self.get_valid_data(post)
        data["comment"] = "X" * (COMMENT_MAX_LENGTH + 1)
        response = client.post("/post/", data)
        assert "Ensure this value has at most %d characters" % COMMENT_MAX_LENGTH in response.content.decode()

    def test_comment_preview(self, client, post):
        data = self.get_valid_data(post)
        data["preview"] = "Preview"
        response = client.post("/post/", data)
        assert response.status_code == 200
        assert "tree_comments/preview.html" in [t.name for t in response.templates]

    def test_post_comment_format_html_invalid_returns_form_fragment(self, client, post):
        data = self.get_valid_data(post)
        data["comment"] = ""
        response = client.post("/post/?format=html", data)
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/html")
        content = response.content.decode()
        assert 'id="comment-form"' in content
        assert "This field is required." in content

    def test_post_comment_format_html_valid_returns_comment_fragment(self, client, post):
        data = self.get_valid_data(post)
        response = client.post("/post/?format=HTML", data)
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/html")
        comment = Comment.objects.get()
        content = response.content.decode()
        assert f'id="c{comment.id}"' in content
        assert "This is my comment" in content

    def test_post_comment_format_non_html_keeps_redirect_logic(self, client, post):
        data = self.get_valid_data(post)
        response = client.post("/post/?format=json", data)
        assert response.status_code == 302

    def test_hash_tampering(self, client, post):
        data = self.get_valid_data(post)
        data["security_hash"] = "Nobody expects the Spanish Inquisition!"
        response = client.post("/post/", data)
        assert response.status_code == 400

    def test_debug_comment_errors(self, client, post, settings):
        """The debug error template should be shown only if DEBUG is True"""
        olddebug = settings.DEBUG

        settings.DEBUG = True
        data = self.get_valid_data(post)
        data["security_hash"] = "Nobody expects the Spanish Inquisition!"
        response = client.post("/post/", data)
        assert response.status_code == 400
        assert "tree_comments/400-debug.html" in [t.name for t in response.templates]

        settings.DEBUG = False
        response = client.post("/post/", data)
        assert response.status_code == 400
        assert "tree_comments/400-debug.html" not in [t.name for t in response.templates]

        settings.DEBUG = olddebug

    def test_create_valid_comment(self, client, post):
        address = "1.2.3.4"
        data = self.get_valid_data(post)
        response = client.post("/post/", data, REMOTE_ADDR=address)
        assert response.status_code == 302
        assert Comment.objects.count() == 1
        c = Comment.objects.first()
        assert c.ip_address == address
        assert c.comment == "This is my comment"

    def test_create_valid_comment_ipv6(self, client, post):
        """
        Test creating a valid comment with a long IPv6 address.
        Note that this test should fail when Comment.ip_address is an IPAddress instead of a GenericIPAddress,
        but does not do so on SQLite or PostgreSQL, because they use the TEXT and INET types, which already
        allow storing an IPv6 address internally.
        """
        address = "2a02::223:6cff:fe8a:2e8a"
        data = self.get_valid_data(post)
        response = client.post("/post/", data, REMOTE_ADDR=address)
        assert response.status_code == 302
        assert Comment.objects.count() == 1
        c = Comment.objects.first()
        assert c.ip_address == address
        assert c.comment == "This is my comment"

    def test_create_valid_comment_no_ip(self, client, post):
        """Empty REMOTE_ADDR value should always set a null ip_address value."""
        data = self.get_valid_data(post)
        for address in ("", None, b""):
            client.post("/post/", data, REMOTE_ADDR=address)
            c = Comment.objects.last()
            assert c.ip_address is None

    def test_create_valid_comment_ipv6_unpack(self, client, post):
        address = "::ffff:18.52.18.52"
        data = self.get_valid_data(post)
        response = client.post("/post/", data, REMOTE_ADDR=address)
        assert response.status_code == 302
        assert Comment.objects.count() == 1
        c = Comment.objects.first()
        # We trim the '::ffff:' bit off because it is an IPv4 addr
        assert c.ip_address == address[7:]
        assert c.comment == "This is my comment"

    def test_post_as_authenticated_user(self, client, post, admin_user):
        data = self.get_valid_data(post)
        data["name"] = data["email"] = ""
        client.force_login(admin_user)
        response = client.post("/post/", data, REMOTE_ADDR="1.2.3.4")
        assert response.status_code == 302
        assert Comment.objects.count() == 1
        c = Comment.objects.first()
        assert c.ip_address == "1.2.3.4"
        assert c.user == admin_user
        assert c.user_name == "admin"
        assert c.user_email == admin_user.email

    def test_post_as_authenticated_user_without_fullname(self, client, post, django_user_model):
        """
        Check that the user's name in the comment is populated for
        authenticated users without first_name and last_name.
        """
        user = django_user_model.objects.create_user(
            username="jane_other", email="jane@example.com", password="jane_other"
        )
        data = self.get_valid_data(post)
        data["name"] = data["email"] = ""
        client.login(username="jane_other", password="jane_other")
        client.post("/post/", data, REMOTE_ADDR="1.2.3.4")
        c = Comment.objects.get(user=user)
        assert c.ip_address == "1.2.3.4"
        assert c.user_name == "jane_other"
        user.delete()

    def test_prevent_duplicate_comments(self, client, post):
        """Prevent posting the exact same comment twice"""
        data = self.get_valid_data(post)
        client.post("/post/", data)
        client.post("/post/", data)
        assert Comment.objects.count() == 1

        # This should not trigger the duplicate prevention
        client.post("/post/", dict(data, comment="My second comment."))
        assert Comment.objects.count() == 2

    def test_comment_signals(self, client, post):
        """Test signals emitted by the comment posting view"""

        # callback
        def receive(sender, **kwargs):
            assert kwargs["comment"].comment == "This is my comment"
            assert "request" in kwargs
            received_signals.append(kwargs.get("signal"))

        # Connect signals and keep track of handled ones
        received_signals = []
        expected_signals = [signals.comment_will_be_posted, signals.comment_was_posted]
        for signal in expected_signals:
            signal.connect(receive)

        # Post a comment and check the signals
        self.test_create_valid_comment(client, post)
        assert received_signals == expected_signals

        for signal in expected_signals:
            signal.disconnect(receive)

    def test_will_be_posted_signal(self, client, post):
        """
        Test that the comment_will_be_posted signal can prevent the comment from
        actually getting saved
        """

        def receive(sender, **kwargs):
            return False

        signals.comment_will_be_posted.connect(receive, dispatch_uid="comment-test")
        data = self.get_valid_data(post)
        response = client.post("/post/", data)
        assert response.status_code == 400
        assert Comment.objects.count() == 0
        signals.comment_will_be_posted.disconnect(dispatch_uid="comment-test")

    def test_will_be_posted_signal_modify_comment(self, client, post):
        """
        Test that the comment_will_be_posted signal can modify a comment before
        it gets posted
        """

        def receive(sender, **kwargs):
            # a bad but effective spam filter :)...
            kwargs["comment"].is_public = False

        signals.comment_will_be_posted.connect(receive)
        self.test_create_valid_comment(client, post)
        c = Comment.objects.first()
        assert not c.is_public

    def test_comment_next(self, client, post):
        """Test the different \"next\" actions the comment view can take"""
        data = self.get_valid_data(post)
        response = client.post("/post/", data)
        expected_url = "/posted/?c=%s" % Comment.objects.latest("id").pk
        assert response.status_code == 302
        assert response.url == expected_url

        data["next"] = "/somewhere/else/"
        data["comment"] = "This is another comment"
        response = client.post("/post/", data)
        expected_url = "/somewhere/else/?c=%s" % Comment.objects.latest("id").pk
        assert response.status_code == 302
        assert response.url == expected_url

        data["next"] = "http://badserver/somewhere/else/"
        data["comment"] = "This is another comment with an unsafe next url"
        response = client.post("/post/", data)
        expected_url = "/posted/?c=%s" % Comment.objects.latest("id").pk
        assert response.status_code == 302
        assert response.url == expected_url

    def test_comment_done_view(self, client, post):
        data = self.get_valid_data(post)
        response = client.post("/post/", data)
        comment = Comment.objects.latest("id")
        location = "/posted/?c=%s" % comment.pk
        assert response.status_code == 302
        assert response.url == location

        response = client.get(location)
        assert "tree_comments/posted.html" in [t.name for t in response.templates]
        assert response.context["comment"] == comment

    def test_comment_next_with_query_string(self, client, post):
        """
        The `next` key needs to handle already having a query string (#10585)
        """
        data = self.get_valid_data(post)
        data["next"] = "/somewhere/else/?foo=bar"
        data["comment"] = "This is another comment"
        response = client.post("/post/", data)
        expected_url = "/somewhere/else/?foo=bar&c=%s" % Comment.objects.latest("id").pk
        assert response.status_code == 302
        assert response.url == expected_url

    def test_comment_post_redirect_with_invalid_integer_pk(self, client, post):
        """
        Tests that attempting to retrieve the location specified in the
        post redirect, after adding some invalid data to the expected
        querystring it ends with, doesn't cause a server error.
        """
        data = self.get_valid_data(post)
        data["comment"] = "This is another comment"
        response = client.post("/post/", data)
        location = response["Location"]
        broken_location = location + "\ufffd"
        response = client.get(broken_location)
        assert response.status_code == 200

    def test_comment_next_with_query_string_and_anchor(self, client, post):
        """
        The `next` key needs to handle already having an anchor. Refs #13411.
        """
        # With a query string also.
        data = self.get_valid_data(post)
        data["next"] = "/somewhere/else/?foo=bar#baz"
        data["comment"] = "This is another comment"
        response = client.post("/post/", data)
        expected_url = "/somewhere/else/?foo=bar&c=%s#baz" % Comment.objects.latest("id").pk
        assert response.status_code == 302
        assert response.url == expected_url


@pytest.mark.django_db
class TestCommentFormTemplateView:
    def get_params(self, post):
        return {
            "content_type": str(Post._meta),
            "object_pk": str(post.pk),
        }

    def test_form_html_render(self, client, post):
        params = self.get_params(post)
        response = client.get("/form/", params)
        assert response.status_code == 200
        # Content-Type should be HTML
        assert response.headers["Content-Type"].startswith("text/html")
        assert "tree_comments/form.html" in [t.name for t in response.templates]

    def test_form_json_render(self, client, post):
        params = self.get_params(post)
        response = client.get("/form/", params, HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        # Content-Type should be JSON
        assert response.headers["Content-Type"].startswith("application/json")
        data = response.json()

        # Must contain important keys from security + details
        for key in (
            "content_type",
            "object_pk",
            "timestamp",
            "security_hash",
            "parent",
            "name",
            "email",
            "url",
            "comment",
            "honeypot",
        ):
            assert key in data

        # Value checks
        assert data["content_type"] == str(Post._meta)
        assert data["object_pk"] == str(post.pk)
        assert str(data["timestamp"]).isdigit()
        assert isinstance(data["security_hash"], str) and len(data["security_hash"]) == 40

    def test_form_missing_params(self, client):
        response = client.get("/form/")
        assert response.status_code == 400

    def test_form_invalid_content_type(self, client, post):
        params = {"content_type": "invalid.module", "object_pk": str(post.pk)}
        response = client.get("/form/", params)
        assert response.status_code == 400

    def test_form_nonexistent_object_pk(self, client, post):
        params = {"content_type": str(Post._meta), "object_pk": "999999"}
        response = client.get("/form/", params)
        assert response.status_code == 400

    def test_form_accept_wildcard_application(self, client, post):
        params = self.get_params(post)
        response = client.get("/form/", params, HTTP_ACCEPT="application/*")
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/html")
        assert "tree_comments/form.html" in [t.name for t in response.templates]

    def test_form_accept_json_with_params(self, client, post):
        params = self.get_params(post)
        response = client.get(
            "/form/",
            params,
            HTTP_ACCEPT="application/json; charset=utf-8",
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("application/json")
        data = response.json()
        assert data["content_type"] == str(Post._meta)
        assert data["object_pk"] == str(post.pk)

    def test_form_accept_multiple(self, client, post):
        params = self.get_params(post)
        response = client.get(
            "/form/",
            params,
            HTTP_ACCEPT="application/json, text/html;q=0.8",
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("application/json")

    def test_form_json_defaults_none(self, client, post):
        params = self.get_params(post)
        response = client.get("/form/", params, HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        data = response.json()
        for key in ("parent", "name", "email", "url", "comment", "honeypot"):
            assert key in data
            assert data[key] is None


@pytest.mark.django_db
class TestCommentModerationViews:
    def make_moderator(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="moderator", email="moderator@example.com", password="moderator"
        )
        comment_model = get_comment_model()
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(comment_model),
            codename="can_moderate",
        )
        user.user_permissions.add(perm)
        return user

    def test_flag_permissions(self, client, comment):
        response = client.get(f"/flag/{comment.pk}/")
        assert response.status_code == 302

    def test_flag_get(self, client, comment, admin_user):
        client.force_login(admin_user)
        response = client.get(f"/flag/{comment.pk}/")
        assert response.status_code == 200
        assert "tree_comments/flag.html" in [t.name for t in response.templates]

    def test_flag_post_creates_flag_and_emits_signal(self, client, comment, admin_user):
        client.force_login(admin_user)
        flag_model = get_comment_flag_model()

        received = []

        def receive(sender, **kwargs):
            received.append(kwargs.get("signal"))
            assert kwargs["comment"].pk == comment.pk
            assert kwargs["request"].user == admin_user
            assert kwargs["flag"].flag == flag_model.SUGGEST_REMOVAL

        signals.comment_was_flagged.connect(receive, dispatch_uid="flag-test")
        response = client.post(f"/flag/{comment.pk}/")
        assert response.status_code == 302
        assert response.url == f"/flagged/?c={comment.pk}"
        assert flag_model.objects.filter(comment=comment, user=admin_user, flag=flag_model.SUGGEST_REMOVAL).count() == 1
        assert received == [signals.comment_was_flagged]
        signals.comment_was_flagged.disconnect(dispatch_uid="flag-test")

    def test_flag_post_is_idempotent(self, client, comment, admin_user):
        client.force_login(admin_user)
        flag_model = get_comment_flag_model()
        client.post(f"/flag/{comment.pk}/")
        client.post(f"/flag/{comment.pk}/")
        assert flag_model.objects.filter(comment=comment, user=admin_user, flag=flag_model.SUGGEST_REMOVAL).count() == 1

    def test_flag_post_safe_next(self, client, comment, admin_user):
        client.force_login(admin_user)
        response = client.post(f"/flag/{comment.pk}/", data={"next": "/go/here/"})
        assert response.status_code == 302
        assert response.url == f"/go/here/?c={comment.pk}"

    def test_flag_post_unsafe_next(self, client, comment, admin_user):
        client.force_login(admin_user)
        response = client.post(f"/flag/{comment.pk}/", data={"next": "http://elsewhere/bad"})
        assert response.status_code == 302
        assert response.url == f"/flagged/?c={comment.pk}"

    def test_flag_done_view(self, client, comment):
        response = client.get("/flagged/", data={"c": comment.pk})
        assert response.status_code == 200
        assert "tree_comments/flagged.html" in [t.name for t in response.templates]

    def test_delete_permissions(self, client, comment, django_user_model):
        response = client.get(f"/delete/{comment.pk}/")
        assert response.status_code == 302

        normal = django_user_model.objects.create_user(username="normal", email="normal@example.com", password="normal")
        client.force_login(normal)
        response = client.get(f"/delete/{comment.pk}/")
        assert response.status_code == 403

        moderator = self.make_moderator(django_user_model)
        client.force_login(moderator)
        response = client.get(f"/delete/{comment.pk}/")
        assert response.status_code == 200
        assert "tree_comments/delete.html" in [t.name for t in response.templates]

    def test_delete_post_updates_comment_and_creates_flag(self, client, comment, django_user_model):
        moderator = self.make_moderator(django_user_model)
        client.force_login(moderator)
        flag_model = get_comment_flag_model()

        response = client.post(f"/delete/{comment.pk}/")
        assert response.status_code == 302
        assert response.url == f"/deleted/?c={comment.pk}"

        comment.refresh_from_db()
        assert comment.is_removed is True
        assert (
            flag_model.objects.filter(comment=comment, user=moderator, flag=flag_model.MODERATOR_DELETION).count() == 1
        )

    def test_delete_done_view(self, client, comment):
        response = client.get("/deleted/", data={"c": comment.pk})
        assert response.status_code == 200
        assert "tree_comments/deleted.html" in [t.name for t in response.templates]

    def test_approve_permissions(self, client, comment, django_user_model):
        response = client.get(f"/approve/{comment.pk}/")
        assert response.status_code == 302

        normal = django_user_model.objects.create_user(
            username="normal2", email="normal2@example.com", password="normal2"
        )
        client.force_login(normal)
        response = client.get(f"/approve/{comment.pk}/")
        assert response.status_code == 403

        moderator = self.make_moderator(django_user_model)
        client.force_login(moderator)
        response = client.get(f"/approve/{comment.pk}/")
        assert response.status_code == 200
        assert "tree_comments/approve.html" in [t.name for t in response.templates]

    def test_approve_post_updates_comment_and_creates_flag(self, client, comment, django_user_model):
        comment.is_removed = True
        comment.is_public = False
        comment.save(update_fields=["is_removed", "is_public"])

        moderator = self.make_moderator(django_user_model)
        client.force_login(moderator)
        flag_model = get_comment_flag_model()

        response = client.post(f"/approve/{comment.pk}/")
        assert response.status_code == 302
        assert response.url == f"/approved/?c={comment.pk}"

        comment.refresh_from_db()
        assert comment.is_removed is False
        assert comment.is_public is True
        assert (
            flag_model.objects.filter(comment=comment, user=moderator, flag=flag_model.MODERATOR_APPROVAL).count() == 1
        )

    def test_approve_done_view(self, client, comment):
        response = client.get("/approved/", data={"c": comment.pk})
        assert response.status_code == 200
        assert "tree_comments/approved.html" in [t.name for t in response.templates]
