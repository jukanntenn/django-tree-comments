from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, IntegerField, Value
from django.utils.encoding import force_str
from django_cte import CTE, with_cte


class CommentQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(is_public=True, is_removed=False)

    def roots(self):
        # Return only visible root-level comments
        return self.visible().filter(parent__isnull=True)


class CommentManager(models.Manager):
    def get_queryset(self):
        return CommentQuerySet(self.model, using=self._db)

    def in_moderation(self):
        """
        QuerySet for all comments currently in the moderation queue.
        """
        return self.get_queryset().filter(is_public=False, is_removed=False)

    def for_model(self, model):
        """
        QuerySet for all comments for a particular model (either an instance or
        a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_queryset().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_str(model._get_pk_val()))
        return qs

    def visible(self):
        return self.get_queryset().visible()

    def roots(self):
        return self.get_queryset().roots()

    def cte_for_instance(self, instance):
        def make_cte(cte):
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
            # Use the manager's model to avoid early import-time lookups
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

        return with_cte(cte, select=cte.join(self.model, id=cte.col.id)).annotate(
            root_id=cte.col.root_id,
            depth=cte.col.depth,
        )

    def threaded_for_instance(self, instance):
        return self.cte_for_instance(instance).order_by("-root_id", "submit_date", "id")
