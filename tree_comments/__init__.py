from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.module_loading import import_string

VERSION = (0, 1, 0)
__version__ = ".".join(map(str, VERSION))

DEFAULT_COMMENTS_APP = "tree_comments"


def get_comment_model():
    attr = "TREE_COMMENTS_COMMENT_MODEL"
    setting = getattr(settings, attr, "tree_comments.Comment")
    try:
        return django_apps.get_model(setting, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(f"{attr} must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            f"{attr} refers to model '{setting}' that has not been installed"
        )


def get_comment_flag_model():
    attr = "TREE_COMMENTS_COMMENT_FLAG_MODEL"
    setting = getattr(settings, attr, "tree_comments.CommentFlag")
    try:
        return django_apps.get_model(setting, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(f"{attr} must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            f"{attr} refers to model '{setting}' that has not been installed"
        )


def get_comment_form():
    attr = "TREE_COMMENTS_COMMENT_FORM"
    setting = getattr(settings, attr, "tree_comments.forms.CommentForm")
    try:
        return import_string(setting)
    except ImportError as e:
        raise ImproperlyConfigured(
            f"{attr} refers to form '{setting}' that could not be imported: {e}"
        )


def get_comment_form_target():
    """
    Returns the target URL for the comment form submission view.
    """
    # TODO: Add support for custom comment form target.
    return reverse("tree-comments-post-comment")
