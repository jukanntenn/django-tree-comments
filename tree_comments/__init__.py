from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

VERSION = (0, 0, 3)
__version__ = ".".join(map(str, VERSION))


def get_comment_model():
    setting = getattr(settings, "TREE_COMMENTS_TREE_COMMENT_MODEL", "tree_comments.TreeComment")
    try:
        return django_apps.get_model(setting, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("TREE_COMMENTS_TREE_COMMENT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "TREE_COMMENTS_TREE_COMMENT_MODEL refers to model '%s' that has not been installed" % setting
        )
