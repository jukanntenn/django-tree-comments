from tests.app.models import SimpleComment


class TestTreeComment:
    def test___str__(self, admin_user, settings):
        comment = SimpleComment(
            content="test content",
            user=admin_user,
        )
        comment.save()
        assert str(comment) == "admin: test content..."

        comment = SimpleComment(content="a" * 100, user=admin_user)
        comment.save()
        truncated = "a" * 50
        assert str(comment) == f"admin: {truncated}..."

    def test_save(self, admin_user, settings):
        comment = SimpleComment(content="test content", user=admin_user)
        comment.save()
        assert comment.created_at is not None
        assert SimpleComment.objects.get(pk=comment.pk).created_at is not None
