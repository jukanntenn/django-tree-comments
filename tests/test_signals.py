from unittest.mock import MagicMock

from django.test import RequestFactory

from tests.app.models import SimpleComment
from tree_comments import signals


def test_comment_posted(admin_user):
    comment = SimpleComment(
        content="test content",
        user=admin_user,
    )
    comment.save()
    rf = RequestFactory()
    request = rf.get("/")
    mock_receiver = MagicMock()
    signals.comment_posted.connect(mock_receiver, sender=SimpleComment)
    signals.comment_posted.send(
        sender=SimpleComment,
        comment=comment,
        request=request,
    )
    mock_receiver.assert_called_once()


def test_comment_edited(admin_user):
    comment = SimpleComment(
        content="test content",
        user=admin_user,
    )
    comment.save()
    rf = RequestFactory()
    request = rf.get("/")
    mock_receiver = MagicMock()
    signals.comment_posted.connect(mock_receiver, sender=SimpleComment)
    signals.comment_posted.send(
        sender=SimpleComment,
        comment=comment,
        request=request,
    )
    mock_receiver.assert_called_once()
