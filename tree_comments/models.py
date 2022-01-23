from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from tree_queries.models import TreeNode


class AbstractTreeComment(TreeNode):
    content = models.TextField(_("content"))
    created_at = models.DateTimeField(_("created at"), default=None)
    ip_address = models.GenericIPAddressField(_("IP address"), unpack_ipv4=True, blank=True, null=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        related_name="comments",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        verbose_name = _("tree comment")
        verbose_name_plural = _("tree comments")

    def __str__(self):
        return "%s: %s..." % (self.user, self.content[:50])

    def save(self, *args, **kwargs):
        if self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)


class TreeComment(AbstractTreeComment):
    class Meta(AbstractTreeComment.Meta):
        swappable = "TREE_COMMENTS_COMMENT_MODEL"
