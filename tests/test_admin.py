import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from tree_comments import get_comment_flag_model, get_comment_model
from tree_comments.admin import CommentsAdmin


@pytest.mark.django_db
class TestCommentsAdminActions:
    def build_request(self, user):
        request = RequestFactory().post("/admin/tree-comments/comment/")
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def make_moderator(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="moderator", email="moderator@example.com", password="moderator"
        )
        comment_model = get_comment_model()
        perm = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(comment_model),
            codename="can_moderate",
        )
        user.user_permissions.add(perm)
        return user

    def test_get_actions_filters_by_permissions(self, django_user_model):
        comment_model = get_comment_model()
        comments_admin = CommentsAdmin(comment_model, admin.site)

        normal = django_user_model.objects.create_user(username="normal", email="normal@example.com", password="normal")
        request = self.build_request(normal)
        actions = comments_admin.get_actions(request)
        assert "flag_comments" in actions
        assert "approve_comments" not in actions
        assert "remove_comments" not in actions
        assert "delete_selected" not in actions

    def test_get_actions_includes_moderation_actions_for_moderator(self, django_user_model):
        comment_model = get_comment_model()
        comments_admin = CommentsAdmin(comment_model, admin.site)

        moderator = self.make_moderator(django_user_model)
        request = self.build_request(moderator)
        actions = comments_admin.get_actions(request)
        assert "flag_comments" in actions
        assert "approve_comments" in actions
        assert "remove_comments" in actions

    def test_flag_comments_action_creates_flags(self, comment, admin_user):
        comment_model = get_comment_model()
        comments_admin = CommentsAdmin(comment_model, admin.site)
        request = self.build_request(admin_user)

        flag_model = get_comment_flag_model()
        assert flag_model.objects.count() == 0

        comments_admin.flag_comments(request, comment_model.objects.filter(pk=comment.pk))
        assert flag_model.objects.filter(comment=comment, user=admin_user, flag=flag_model.SUGGEST_REMOVAL).count() == 1

        messages = list(m.message for m in request._messages)
        assert "1 comment was successfully flagged." in messages

    def test_remove_comments_action_marks_removed(self, comment, django_user_model):
        comment_model = get_comment_model()
        comments_admin = CommentsAdmin(comment_model, admin.site)
        moderator = self.make_moderator(django_user_model)
        request = self.build_request(moderator)
        flag_model = get_comment_flag_model()

        comments_admin.remove_comments(request, comment_model.objects.filter(pk=comment.pk))
        comment.refresh_from_db()
        assert comment.is_removed is True
        assert (
            flag_model.objects.filter(
                comment=comment,
                user=moderator,
                flag=flag_model.MODERATOR_DELETION,
            ).count()
            == 1
        )

        messages = list(m.message for m in request._messages)
        assert "1 comment was successfully removed." in messages

    def test_approve_comments_action_marks_public(self, comment, django_user_model):
        comment_model = get_comment_model()
        comments_admin = CommentsAdmin(comment_model, admin.site)
        moderator = self.make_moderator(django_user_model)
        request = self.build_request(moderator)
        flag_model = get_comment_flag_model()

        comment.is_removed = True
        comment.is_public = False
        comment.save(update_fields=["is_removed", "is_public"])

        comments_admin.approve_comments(request, comment_model.objects.filter(pk=comment.pk))
        comment.refresh_from_db()
        assert comment.is_removed is False
        assert comment.is_public is True
        assert (
            flag_model.objects.filter(
                comment=comment,
                user=moderator,
                flag=flag_model.MODERATOR_APPROVAL,
            ).count()
            == 1
        )

        messages = list(m.message for m in request._messages)
        assert "1 comment was successfully approved." in messages
