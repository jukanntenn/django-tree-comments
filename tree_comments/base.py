from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class AbstractBaseComment(models.Model):
    """
    An abstract base class that any custom comment models probably should
    subclass.
    """

    # Content-object field
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        related_name="content_type_set_for_%(class)s",
        on_delete=models.CASCADE,
    )
    object_pk = models.CharField(_("object ID"), db_index=True, max_length=64)
    content_object = GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    # Metadata about the comment
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    # TODO: test
    def get_content_object_url(self) -> str:
        """
        Get a URL suitable for redirecting to the content object.
        """
        return reverse("tree-comments-url-redirect", args=(self.content_type_id, self.object_pk))
