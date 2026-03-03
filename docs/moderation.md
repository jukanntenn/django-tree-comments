# Moderation

Comment moderation system for managing user comments.

## Overview

Django Tree Comments includes a moderation system for:

- Flagging inappropriate comments
- Approving/removing comments
- Email notifications for moderators

## Comment Flags

Users can flag comments for moderator review.

### Flag Types

- **Suggest Removal** - User suggests the comment should be removed
- **Moderator Deletion** - Moderator deleted the comment

### Flagging a Comment

```python
from tree_comments.models import CommentFlag

flag = CommentFlag.objects.create(
    user=request.user,
    comment=comment,
    flag=CommentFlag.SUGGEST_REMOVAL
)
```

## Moderator Actions

### Approve Comment

```python
comment.is_public = True
comment.save()
```

### Remove Comment

```python
comment.is_removed = True
comment.save()
```

## Email Notifications

Configure email notifications for new comments:

```python
from tree_comments.moderation import CommentModerator

class MyModerator(CommentModerator):
    email_notification = True
    auto_moderate_field = 'publish_date'
    moderate_after = 30  # days
```

## Template Tags

Display moderation links:

```django
{% load tree_comments %}

<a href="{% url 'tree-comments-flag' comment.id %}">Flag</a>
{% if user.is_staff %}
    <a href="{% url 'tree-comments-delete' comment.id %}">Delete</a>
    <a href="{% url 'tree-comments-approve' comment.id %}">Approve</a>
{% endif %}
```

## Views

### FlagCommentView

Allows users to flag comments.

### DeleteCommentView

Allows moderators to delete comments (requires staff status).

### ApproveCommentView

Allows moderators to approve comments (requires staff status).
