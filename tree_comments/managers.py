from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, IntegerField, Value
from django.utils.encoding import force_str
from django_cte import CTE, with_cte  # type: ignore[import-untyped]
from typing_extensions import Self

if TYPE_CHECKING:
    from .models import Comment


class CommentQuerySet(models.QuerySet["Comment"]):
    def visible(self) -> Self:
        return self.filter(is_public=True, is_removed=False)

    def roots(self) -> Self:
        return self.visible().filter(parent__isnull=True)

    def in_moderation(self) -> Self:
        """QuerySet for all comments currently in the moderation queue."""
        return self.filter(is_public=False, is_removed=False)

    def for_model(self, model: models.Model | type[models.Model]) -> Self:
        """QuerySet for all comments for a particular model (either an instance or a class)."""
        ct = ContentType.objects.get_for_model(model)
        qs: Self = self.filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_str(model._get_pk_val()))
        return qs

    def cte_for_instance(self, instance: models.Model | type[models.Model]) -> Self:
        def make_cte(cte: CTE) -> models.QuerySet[Comment]:
            base = (
                self.for_model(instance)
                .roots()
                .visible()
                .annotate(
                    root_id=F("id"),
                    depth=Value(0, output_field=IntegerField()),
                )
                .order_by()
            )
            recursive = (
                cte.join(self.model, parent=cte.col.id)
                .annotate(
                    root_id=cte.col.root_id,
                    depth=cte.col.depth + Value(1, output_field=IntegerField()),
                )
                .order_by()
            )
            return base.union(recursive, all=True)

        cte = CTE.recursive(make_cte)

        # Direct CTE column selection avoids a redundant INNER JOIN.
        # See docs/plans/2026-07-04-perf-optimization-plan.md plan A.
        return with_cte(cte, select=cte).annotate(  # type: ignore[no-any-return]
            root_id=cte.col.root_id,
            depth=cte.col.depth,
        )

    def threaded_for_instance(self, instance: models.Model | type[models.Model]) -> Self:
        return (
            self.cte_for_instance(instance)
            .select_related("parent", "user", "content_type")
            .order_by("-root_id", "submit_date", "id")
        )


CommentManager = models.Manager.from_queryset(CommentQuerySet)
