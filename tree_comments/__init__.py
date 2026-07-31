from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from django.db.models import Model
    from django.forms import Form

VERSION = (0, 0, 4, "rc", 1)  # PEP 440 release level: "alpha" | "beta" | "rc" | "final"
__version__ = "0.0.4rc1"

DEFAULT_COMMENTS_APP = "tree_comments"


def get_comment_model() -> type[Model]:
    attr = "TREE_COMMENTS_COMMENT_MODEL"
    setting = getattr(settings, attr, "tree_comments.Comment")
    try:
        return django_apps.get_model(setting, require_ready=False)
    except ValueError as err:
        raise ImproperlyConfigured(f"{attr} must be of the form 'app_label.model_name'") from err
    except LookupError as err:
        raise ImproperlyConfigured(f"{attr} refers to model '{setting}' that has not been installed") from err


def get_comment_flag_model() -> type[Model]:
    attr = "TREE_COMMENTS_COMMENT_FLAG_MODEL"
    setting = getattr(settings, attr, "tree_comments.CommentFlag")
    try:
        return django_apps.get_model(setting, require_ready=False)
    except ValueError as err:
        raise ImproperlyConfigured(f"{attr} must be of the form 'app_label.model_name'") from err
    except LookupError as err:
        raise ImproperlyConfigured(f"{attr} refers to model '{setting}' that has not been installed") from err


def get_comment_form() -> type[Form]:
    attr = "TREE_COMMENTS_COMMENT_FORM"
    setting = getattr(settings, attr, "tree_comments.forms.CommentForm")
    try:
        result: type[Form] = import_string(setting)
        return result
    except ImportError as e:
        raise ImproperlyConfigured(f"{attr} refers to form '{setting}' that could not be imported: {e}") from e


def get_comment_form_target() -> str:
    """Return the target URL for the comment form submission view."""
    return reverse("tree-comments-post-comment")


def get_flag_url(comment: Any) -> str:
    """Get the URL for the "flag this comment" view."""
    return reverse("tree-comments-flag", args=(comment.id,))


def get_delete_url(comment: Any) -> str:
    """Get the URL for the "delete this comment" view."""
    return reverse("tree-comments-delete", args=(comment.id,))


def get_approve_url(comment: Any) -> str:
    """Get the URL for the "approve this comment from moderation" view."""
    return reverse("tree-comments-approve", args=(comment.id,))
