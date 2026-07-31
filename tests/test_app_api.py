"""
Tests for the public API functions and swappable model support.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from tree_comments import (
    get_approve_url,
    get_comment_flag_model,
    get_comment_form,
    get_comment_form_target,
    get_comment_model,
    get_delete_url,
    get_flag_url,
)


class TestGetCommentModel:
    """Tests for get_comment_model() function."""

    def test_default_model(self):
        """Test that default model is tree_comments.Comment."""
        model = get_comment_model()
        assert model.__name__ == "Comment"
        assert model._meta.app_label == "tree_comments"

    def test_invalid_model_format(self, settings):
        """Test that invalid format raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_MODEL = "InvalidFormat"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_model()
        assert "must be of the form" in str(exc.value)

    def test_nonexistent_model(self, settings):
        """Test that nonexistent model raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_MODEL = "nonexistent.Model"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_model()
        assert "has not been installed" in str(exc.value)


class TestGetCommentFlagModel:
    """Tests for get_comment_flag_model() function."""

    def test_default_model(self):
        """Test that default model is tree_comments.CommentFlag."""
        model = get_comment_flag_model()
        assert model.__name__ == "CommentFlag"
        assert model._meta.app_label == "tree_comments"

    def test_invalid_model_format(self, settings):
        """Test that invalid format raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_FLAG_MODEL = "InvalidFormat"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_flag_model()
        assert "must be of the form" in str(exc.value)


class TestGetCommentForm:
    """Tests for get_comment_form() function."""

    def test_default_form(self):
        """Test that default form is CommentForm."""
        form = get_comment_form()
        assert form.__name__ == "CommentForm"

    def test_custom_form_setting(self, settings):
        """Test custom form via TREE_COMMENTS_COMMENT_FORM."""
        settings.TREE_COMMENTS_COMMENT_FORM = "tree_comments.forms.CommentDetailsForm"
        form = get_comment_form()
        assert form.__name__ == "CommentDetailsForm"

    def test_invalid_form_import(self, settings):
        """Test that invalid form raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_FORM = "nonexistent.Form"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_form()
        assert "could not be imported" in str(exc.value)


class TestGetCommentFormTarget:
    """Tests for get_comment_form_target() function."""

    def test_returns_url(self):
        """Test that function returns correct URL."""
        url = get_comment_form_target()
        expected = reverse("tree-comments-post-comment")
        assert url == expected


class TestGetFlagUrl:
    """Tests for get_flag_url() function."""

    @pytest.mark.django_db
    def test_returns_correct_url(self, comment):
        """Test that function returns correct flag URL."""
        url = get_flag_url(comment)
        expected = reverse("tree-comments-flag", args=(comment.id,))
        assert url == expected

    @pytest.mark.django_db
    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_flag_url(comment)
        assert str(comment.id) in url


class TestGetDeleteUrl:
    """Tests for get_delete_url() function."""

    @pytest.mark.django_db
    def test_returns_correct_url(self, comment):
        """Test that function returns correct delete URL."""
        url = get_delete_url(comment)
        expected = reverse("tree-comments-delete", args=(comment.id,))
        assert url == expected

    @pytest.mark.django_db
    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_delete_url(comment)
        assert str(comment.id) in url


class TestGetApproveUrl:
    """Tests for get_approve_url() function."""

    @pytest.mark.django_db
    def test_returns_correct_url(self, comment):
        """Test that function returns correct approve URL."""
        url = get_approve_url(comment)
        expected = reverse("tree-comments-approve", args=(comment.id,))
        assert url == expected

    @pytest.mark.django_db
    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_approve_url(comment)
        assert str(comment.id) in url
