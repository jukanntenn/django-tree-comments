import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.template import Context, Template
from django.test.client import RequestFactory
from django.test.utils import override_settings

from tree_comments.forms import CommentForm
from tree_comments.models import Comment

from .app.models import Post

User = get_user_model()


@pytest.mark.django_db
class TestTemplateTags:
    def create_some_comments(self):
        site = Site.objects.get_current()
        user = User.objects.create_user(username="alice")
        post = Post.objects.create(title="test post", author=user)

        post_ctype = ContentType.objects.get_for_model(Post)

        self.post = post

        self.c1 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            user_name="alice",
            comment="test comment 1",
            is_public=True,
            is_removed=False,
        )

        self.c2 = Comment.objects.create(
            content_type=post_ctype,
            object_pk=post.pk,
            site=site,
            user=user,
            user_name="alice",
            comment="test comment 2",
            is_public=True,
            is_removed=False,
        )

    def render(self, t, **c):
        """Render a template with given context."""
        ctx = Context(c)
        out = Template(t).render(ctx)
        return ctx, out

    def test_comment_form_target(self):
        """Test comment_form_target tag."""
        _, out = self.render("{% load tree_comments %}{% comment_form_target %}")
        assert out == "/post/"

    def test_get_comment_form(self, post, tag=None):
        """Test get_comment_form tag."""
        t = "{% load tree_comments %}" + (
            tag or "{% get_comment_form for app.post p.id as form %}"
        )
        ctx, out = self.render(t, p=post)
        assert out == ""
        assert isinstance(ctx["form"], CommentForm)

    def test_get_comment_form_from_literal(self, post):
        """Test get_comment_form tag with literal object."""
        self.test_get_comment_form(
            post, tag="{% get_comment_form for app.post 1 as form %}"
        )

    def test_get_comment_form_from_object(self, post):
        """Test get_comment_form tag with object instance."""
        self.test_get_comment_form(post, tag="{% get_comment_form for p as form %}")

    def test_whitespace_in_get_comment_form_tag(self, post):
        """Test get_comment_form tag with whitespace handling."""
        self.test_get_comment_form(
            post,
            tag="{% load comment_testtags %}{% get_comment_form for p|noop:'x y' as form %}",
        )

    def test_render_comment_form(self, post, tag=None):
        """Test render_comment_form tag."""
        t = "{% load tree_comments %}" + (
            tag or "{% render_comment_form for app.post p.id %}"
        )

        ctx, out = self.render(t, p=post)
        assert out.strip().startswith("<form action=")
        assert out.strip().endswith("</form>")

    def test_render_comment_form_from_literal(self, post):
        """Test render_comment_form tag with literal object."""
        self.test_render_comment_form(
            post, tag="{% render_comment_form for app.post 1 %}"
        )

    def test_render_comment_form_from_object(self, post):
        """Test render_comment_form tag with object instance."""
        self.test_render_comment_form(post, tag="{% render_comment_form for p %}")

    def test_whitespace_in_render_comment_form_tag(self, post):
        """Test render_comment_form tag with whitespace handling."""
        self.test_render_comment_form(
            post,
            tag="{% load comment_testtags %}{% render_comment_form for p|noop:'x y' %}",
        )

    def test_render_comment_form_from_object_with_query_count(
        self, django_assert_num_queries, post
    ):
        """Test render_comment_form with query counting."""
        with django_assert_num_queries(0):
            self.test_render_comment_form_from_object(post)

    def verify_get_comment_count(self, tag=None):
        """Helper method to verify comment count functionality."""
        t = (
            "{% load tree_comments %}"
            + (tag or "{% get_comment_count for app.post p.id as cc %}")
            + "{{ cc }}"
        )
        ctx, out = self.render(t, p=self.post)
        assert out == "2"

    def test_get_comment_count(self):
        """Test get_comment_count tag."""
        self.create_some_comments()
        self.verify_get_comment_count("{% get_comment_count for app.post p.id as cc %}")

    def test_get_comment_count_from_literal(self):
        """Test get_comment_count tag with literal object."""
        self.create_some_comments()
        self.verify_get_comment_count("{% get_comment_count for app.post 1 as cc %}")

    def test_get_comment_count_from_object(self):
        """Test get_comment_count tag with object instance."""
        self.create_some_comments()
        self.verify_get_comment_count("{% get_comment_count for p as cc %}")

    def test_whitespace_in_get_comment_count_tag(self):
        """Test get_comment_count tag with whitespace handling."""
        self.create_some_comments()
        self.verify_get_comment_count(
            "{% load comment_testtags %}{% get_comment_count for p|noop:'x y' as cc %}"
        )

    def verify_get_comment_list(self, tag=None):
        """Helper method to verify comment list functionality."""
        Comment.objects.all()[:4]
        t = "{% load tree_comments %}" + (
            tag or "{% get_comment_list for app.post p.id as cl %}"
        )
        ctx, out = self.render(t, p=self.post)
        assert out == ""
        assert list(ctx["cl"]) == [self.c1, self.c2]

    def test_get_comment_list(self):
        """Test get_comment_list tag."""
        self.create_some_comments()
        self.verify_get_comment_list("{% get_comment_list for app.post p.id as cl %}")

    def test_get_comment_list_from_literal(self):
        """Test get_comment_list tag with literal object."""
        self.create_some_comments()
        self.verify_get_comment_list("{% get_comment_list for app.post p.id as cl %}")

    def test_get_comment_list_from_object(self):
        """Test get_comment_list tag with object instance."""
        self.create_some_comments()
        self.verify_get_comment_list("{% get_comment_list for p as cl %}")

    def test_get_comment_list_using_request(self, tag=None):
        """Test get_comment_list tag using request object."""
        site_2 = Site.objects.create(
            id=settings.SITE_ID + 1, domain="testserver", name="testserver"
        )
        # A request lookup should return site_2
        with override_settings(SITE_ID=site_2.id):
            self.create_some_comments()

        # Effectively unset SITE_ID which forces a site lookup from the
        # request. Create a new comment for the second site.
        with override_settings(SITE_ID=None):
            t = "{% load tree_comments %}" + (
                tag or "{% get_comment_list for app.post p.id as cl %}"
            )
            request = RequestFactory().get("/")
            ctx, out = self.render(t, p=self.post, request=request)
            assert list(ctx["cl"]) == [self.c1, self.c2]

    def test_whitespace_in_get_comment_list_tag(self):
        """Test get_comment_list tag with whitespace handling."""
        self.create_some_comments()
        self.verify_get_comment_list(
            "{% load comment_testtags %}{% get_comment_list for p|noop:'x y' as cl %}"
        )

    def test_get_comment_permalink(self):
        """Test get_comment_permalink tag."""
        self.create_some_comments()
        t = "{% load tree_comments %}{% get_comment_list for app.post p.id as cl %}"
        t += "{% get_comment_permalink cl.0 %}"
        ct = ContentType.objects.get_for_model(Post)
        ctx, out = self.render(t, p=self.post)
        assert out == "/cr/%s/%s/#c%s" % (ct.id, self.post.id, self.c1.id)

    def test_get_comment_permalink_formatted(self):
        """Test get_comment_permalink tag with custom formatting."""
        self.create_some_comments()
        t = "{% load tree_comments %}{% get_comment_list for app.post p.id as cl %}"
        t += "{% get_comment_permalink cl.0 '#c%(id)s-by-%(user_name)s' %}"
        ct = ContentType.objects.get_for_model(Post)
        ctx, out = self.render(t, p=self.post)
        assert out == "/cr/%s/%s/#c%s-by-alice" % (
            ct.id,
            self.post.id,
            self.c1.id,
        )

    def test_whitespace_in_get_comment_permalink_tag(self):
        """Test get_comment_permalink tag with whitespace handling."""
        self.create_some_comments()
        t = "{% load tree_comments comment_testtags %}{% get_comment_list for app.post p.id as cl %}"
        t += "{% get_comment_permalink cl.0|noop:'x y' %}"
        ct = ContentType.objects.get_for_model(Post)
        ctx, out = self.render(t, p=self.post)
        assert out == "/cr/%s/%s/#c%s" % (ct.id, self.post.id, self.c1.id)

    def test_render_comment_list(self, tag=None):
        """Test render_comment_list tag."""
        self.create_some_comments()
        t = "{% load tree_comments %}" + (
            tag or "{% render_comment_list for app.post p.id %}"
        )
        ctx, out = self.render(t, p=self.post)
        assert out.strip().startswith('<dl id="comments">')
        assert out.strip().endswith("</dl>")

    def test_render_comment_list_from_literal(self):
        """Test render_comment_list tag with literal object."""
        self.test_render_comment_list("{% render_comment_list for app.post 1 %}")

    def test_render_comment_list_from_object(self):
        """Test render_comment_list tag with object instance."""
        self.test_render_comment_list("{% render_comment_list for p %}")

    def test_whitespace_in_render_comment_list_tag(self):
        """Test render_comment_list tag with whitespace handling."""
        self.test_render_comment_list(
            "{% load tree_comments comment_testtags %}{% render_comment_list for p|noop:'x y' %}"
        )

    def test_render_comment_app(self, tag=None):
        """Test render_comment_app tag renders app container, form, and threaded list."""
        self.create_some_comments()
        t = "{% load tree_comments %}" + (
            tag or "{% render_comment_app for app.post p.id %}"
        )
        ctx, out = self.render(t, p=self.post)
        assert 'class="tree-comments-app"' in out
        assert 'id="comment-form"' in out
        assert 'id="comments-threaded"' in out
        # Both comments should be present
        assert f'id="c{self.c1.id}"' in out
        assert f'id="c{self.c2.id}"' in out
        # Order should be c2 before c1 (root_id desc)
        assert out.find(f'id="c{self.c2.id}"') < out.find(f'id="c{self.c1.id}"')

    def test_render_comment_app_from_literal(self):
        """Test render_comment_app tag with literal object."""
        self.test_render_comment_app("{% render_comment_app for app.post 1 %}")

    def test_render_comment_app_from_object(self):
        """Test render_comment_app tag with object instance."""
        self.test_render_comment_app("{% render_comment_app for p %}")

    def test_whitespace_in_render_comment_app_tag(self):
        """Test render_comment_app tag with whitespace handling via noop filter."""
        self.test_render_comment_app(
            "{% load tree_comments comment_testtags %}{% render_comment_app for p|noop:'x y' %}"
        )

    def test_render_comment_app_shows_no_comments_when_empty(self):
        """When there are no comments, the app template shows the empty state."""
        user = User.objects.create_user(username="bob")
        p2 = Post.objects.create(title="second post", author=user)
        t = "{% load tree_comments %}{% render_comment_app for app.post p2.id %}"
        ctx, out = self.render(t, p2=p2)
        assert '<p class="no-comments">' in out

    def test_render_comment_app_child_is_indented(self):
        """Child comments should render with the is-child class (indented)."""
        self.create_some_comments()
        child = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_pk=self.post.pk,
            site=Site.objects.get_current(),
            user=self.c1.user,
            comment="child comment",
            is_public=True,
            is_removed=False,
            parent=self.c1,
        )
        t = "{% load tree_comments %}{% render_comment_app for app.post p.id %}"
        ctx, out = self.render(t, p=self.post)
        assert f'id="c{child.id}"' in out
        assert "is-child" in out

    # FIXME
    # def test_number_queries(self, django_assert_num_queries):
    #     """
    #     Ensure that the template tags use cached content types to reduce the
    #     number of DB queries.
    #     Refs #16042.
    #     """
    #     # {% render_comment_list %} -----------------

    #     # Clear CT cache
    #     ContentType.objects.clear_cache()
    #     with django_assert_num_queries(3):
    #         self.test_render_comment_list_from_object()

    #     # CT's should be cached
    #     with django_assert_num_queries(2):
    #         self.test_render_comment_list_from_object()

    #     # {% get_comment_list %} --------------------

    #     ContentType.objects.clear_cache()
    #     with django_assert_num_queries(4):
    #         self.verify_get_comment_list()

    #     with django_assert_num_queries(3):
    #         self.verify_get_comment_list()

    #     # {% render_comment_form %} -----------------

    #     ContentType.objects.clear_cache()
    #     with django_assert_num_queries(3):
    #         self.test_render_comment_form()

    #     with django_assert_num_queries(2):
    #         self.test_render_comment_form()

    #     # {% get_comment_form %} --------------------

    #     ContentType.objects.clear_cache()
    #     with django_assert_num_queries(3):
    #         self.test_get_comment_form()

    #     with django_assert_num_queries(2):
    #         self.test_get_comment_form()

    #     # {% get_comment_count %} -------------------

    #     ContentType.objects.clear_cache()
    #     with django_assert_num_queries(3):
    #         self.verify_get_comment_count()

    #     with django_assert_num_queries(2):
    #         self.verify_get_comment_count()
