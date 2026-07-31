from django import template

from tree_comments import get_comment_model

from ..tree_utils import build_nested

register = template.Library()


@register.filter
def build_nested_for_post(post):
    """Return the nested comment tree for the given post, consumed by app.html.

    Uses the active comment model's (in the custom example, comments.Comment)
    threaded_for_instance to fetch the flat CTE result, then converts it into a
    nested tree.
    """
    flat = get_comment_model().objects.threaded_for_instance(post)
    return build_nested(list(flat))
