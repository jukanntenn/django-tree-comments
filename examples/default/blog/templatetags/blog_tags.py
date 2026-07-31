from django import template

from tree_comments.models import Comment

from ..tree_utils import build_nested

register = template.Library()


@register.filter
def build_nested_for_post(post):
    """Return a nested tree of comments for the given post, ready for app.html."""
    flat = Comment.objects.threaded_for_instance(post)
    return build_nested(list(flat))
