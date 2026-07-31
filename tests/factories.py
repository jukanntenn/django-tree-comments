"""factory_boy factories for test data.

Usage in tests::

    from tests.factories import CommentFactory, PostFactory

    root = CommentFactory(target_object=post, user=admin_user)
    child = CommentFactory(target_object=post, user=admin_user, parent=root)

The ``parent`` field defaults to ``None`` (root comment); pass a parent
instance to create a reply.
"""

import factory
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from tests.app.models import Post
from tree_comments.models import Comment


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Sequence(lambda n: f"Post {n}")
    enable_comments = True


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    # Generic relation fields derived from target_object.
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.target_object))
    object_pk = factory.LazyAttribute(lambda o: str(o.target_object.pk))
    site = factory.LazyAttribute(lambda o: Site.objects.get_current())

    comment = factory.Sequence(lambda n: f"test comment {n}")
    is_public = True
    is_removed = False

    # Self-referential FK: default None (root). Pass parent=root to create a reply.
    parent = None

    class Params:
        # ``target_object`` is the object being commented on. It is excluded
        # from the model fields; it only drives the LazyAttribute declarations.
        target_object = None
