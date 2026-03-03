# Signals

Django signals provided by Django Tree Comments.

## Available Signals

### comment_will_be_posted

Sent before a comment is saved to the database.

**Arguments:**
- `comment` - The comment object
- `request` - The HTTP request

**Usage:**

```python
from tree_comments.signals import comment_will_be_posted

def validate_comment(sender, comment, request, **kwargs):
    if 'spam' in comment.comment.lower():
        raise ValidationError("Spam detected!")

comment_will_be_posted.connect(validate_comment)
```

### comment_was_posted

Sent after a comment is successfully saved.

**Arguments:**
- `comment` - The comment object
- `request` - The HTTP request

**Usage:**

```python
from tree_comments.signals import comment_was_posted

def notify_author(sender, comment, request, **kwargs):
    # Send email notification
    send_notification_email(comment)

comment_was_posted.connect(notify_author)
```

### comment_was_flagged

Sent when a comment is flagged.

**Arguments:**
- `comment` - The comment object
- `flag` - The flag object
- `created` - Whether the flag was created
- `request` - The HTTP request

**Usage:**

```python
from tree_comments.signals import comment_was_flagged

def notify_moderator(sender, comment, flag, created, request, **kwargs):
    if created:
        send_moderator_notification(comment, flag)

comment_was_flagged.connect(notify_moderator)
```

## Signal Flow

1. User submits comment form
2. `comment_will_be_posted` signal fires
3. Comment is validated and saved
4. `comment_was_posted` signal fires
5. User is redirected

## Best Practices

- Keep signal handlers lightweight
- Use async tasks for long-running operations
- Handle exceptions gracefully
- Don't modify the comment in `comment_was_posted` (it's already saved)
