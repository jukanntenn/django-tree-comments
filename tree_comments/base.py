from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils import timezone
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
    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return reverse(
            "tree-comments-url-redirect", args=(self.content_type_id, self.object_pk)
        )


class AbstractCommentFlag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        related_name="comment_flags",
        on_delete=models.CASCADE,
    )
    comment = models.ForeignKey(
        getattr(settings, "TREE_COMMENTS_COMMENT_MODEL", "tree_comments.Comment"),
        verbose_name=_("comment"),
        related_name="flags",
        on_delete=models.CASCADE,
    )
    flag = models.CharField(_("flag"), max_length=30, db_index=True)
    flag_date = models.DateTimeField(_("date"), default=None)

    SUGGEST_REMOVAL = "removal suggestion"
    MODERATOR_DELETION = "moderator deletion"
    MODERATOR_APPROVAL = "moderator approval"

    class Meta:
        abstract = True
        unique_together = [("user", "comment", "flag")]
        verbose_name = _("comment flag")
        verbose_name_plural = _("comment flags")

    def __str__(self):
        return "%s flag of comment ID %s by %s" % (
            self.flag,
            self.comment_id,
            self.user.get_username(),
        )

    def save(self, *args, **kwargs):
        if self.flag_date is None:
            self.flag_date = timezone.now()
        super().save(*args, **kwargs)
