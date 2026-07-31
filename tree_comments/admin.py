from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from tree_comments import get_comment_flag_model, get_comment_model

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


class UsernameSearch:
    """The User object may not be auth.User, so we need to provide
    a mechanism for issuing the equivalent of a .filter(user__username=...)
    search in CommentAdmin.
    """

    def __str__(self) -> str:
        return f"user__{get_user_model().USERNAME_FIELD}"


class CommentsAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    fieldsets = (
        (None, {"fields": ("content_type", "object_pk", "site")}),
        (
            _("Content"),
            {"fields": ("user", "user_name", "user_email", "user_url", "comment")},
        ),
        (
            _("Metadata"),
            {"fields": ("submit_date", "ip_address", "is_public", "is_removed")},
        ),
    )

    list_display = (
        "name",
        "content_type",
        "object_pk",
        "ip_address",
        "submit_date",
        "is_public",
        "is_removed",
    )
    list_filter = ("submit_date", "site", "is_public", "is_removed")
    date_hierarchy = "submit_date"
    ordering = ("-submit_date",)
    raw_id_fields = ("user",)
    search_fields: tuple[str, ...] = (  # type: ignore[misc,assignment]
        "comment",
        UsernameSearch(),
        "user_name",
        "user_email",
        "user_url",
        "ip_address",
    )
    actions = ["flag_comments", "approve_comments", "remove_comments"]  # noqa: RUF012

    def get_moderation_permission(self) -> str:
        return f"{get_comment_model()._meta.app_label}.can_moderate"

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        # Only superusers should be able to delete the comments from the DB.
        if not request.user.is_superuser and "delete_selected" in actions:
            actions.pop("delete_selected")
        if not request.user.has_perm(self.get_moderation_permission()):
            if "approve_comments" in actions:
                actions.pop("approve_comments")
            if "remove_comments" in actions:
                actions.pop("remove_comments")
        return actions

    @admin.action(description=_("Flag selected comments"))
    def flag_comments(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        flag_model: Any = get_comment_flag_model()
        flagged = 0
        for comment in queryset:
            _, created = flag_model.objects.get_or_create(
                comment=comment,
                user=request.user,
                flag=flag_model.SUGGEST_REMOVAL,
            )
            if created:
                flagged += 1
        self.message_user(
            request,
            ngettext(
                "%d comment was successfully flagged.",
                "%d comments were successfully flagged.",
                flagged,
            )
            % flagged,
            messages.SUCCESS,
        )

    @admin.action(description=_("Approve selected comments"))
    def approve_comments(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        flag_model: Any = get_comment_flag_model()
        approved = 0
        for comment in queryset:
            _, created = flag_model.objects.get_or_create(
                comment=comment,
                user=request.user,
                flag=flag_model.MODERATOR_APPROVAL,
            )
            comment.is_removed = False
            comment.is_public = True
            comment.save(update_fields=["is_removed", "is_public"])
            if created:
                approved += 1
        self.message_user(
            request,
            ngettext(
                "%d comment was successfully approved.",
                "%d comments were successfully approved.",
                approved,
            )
            % approved,
            messages.SUCCESS,
        )

    @admin.action(description=_("Remove selected comments"))
    def remove_comments(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        flag_model: Any = get_comment_flag_model()
        removed = 0
        for comment in queryset:
            _, created = flag_model.objects.get_or_create(
                comment=comment,
                user=request.user,
                flag=flag_model.MODERATOR_DELETION,
            )
            comment.is_removed = True
            comment.save(update_fields=["is_removed"])
            if created:
                removed += 1
        self.message_user(
            request,
            ngettext(
                "%d comment was successfully removed.",
                "%d comments were successfully removed.",
                removed,
            )
            % removed,
            messages.SUCCESS,
        )


# Only register the default admin if the model is the built-in comment model
# (this won't be true if there's a custom comment app).
Klass = get_comment_model()
if Klass._meta.app_label == "tree_comments":
    admin.site.register(Klass, CommentsAdmin)
