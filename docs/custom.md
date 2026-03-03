# Custom Apps

How to customize Django Tree Comments with your own models.

## Swappable Models

Django Tree Comments supports swappable models via Django's settings.

### Custom Comment Model

Create your custom model:

```python
# myapp/models.py
from tree_comments.models import AbstractComment

class CustomComment(AbstractComment):
    # Add custom fields
    rating = models.IntegerField(default=5)

    class Meta(AbstractComment.Meta):
        abstract = False
```

Configure in settings:

```python
TREE_COMMENTS_COMMENT_MODEL = 'myapp.CustomComment'
```

### Custom Comment Flag Model

Create your custom flag model:

```python
# myapp/models.py
from tree_comments.models import AbstractCommentFlag

class CustomCommentFlag(AbstractCommentFlag):
    # Add custom fields
    reason = models.TextField()

    class Meta(AbstractCommentFlag.Meta):
        abstract = False
```

Configure in settings:

```python
TREE_COMMENTS_COMMENT_FLAG_MODEL = 'myapp.CustomCommentFlag'
```

## Custom Forms

Create a custom form:

```python
# myapp/forms.py
from tree_comments.forms import CommentDetailsForm

class CustomCommentForm(CommentDetailsForm):
    rating = forms.IntegerField(min_value=1, max_value=5)

    def clean_rating(self):
        rating = self.cleaned_data['rating']
        # Custom validation
        return rating
```

Configure in settings:

```python
TREE_COMMENTS_COMMENT_FORM = 'myapp.forms.CustomCommentForm'
```

## Custom Managers

Extend the CommentManager:

```python
# myapp/managers.py
from tree_comments.managers import CommentManager as BaseCommentManager

class CommentManager(BaseCommentManager):
    def with_ratings(self):
        return self.filter(rating__gte=4)
```

Use in your model:

```python
class CustomComment(AbstractComment):
    objects = CommentManager()
    # ...
```

## Migration Considerations

When creating custom models:

1. Inherit from `AbstractComment` or `AbstractCommentFlag`
2. Set `abstract = False` in Meta
3. Create and run migrations
4. Update settings before running migrations

## Example: Adding User Mentions

```python
from django.db import models
from tree_comments.models import AbstractComment

class Comment(AbstractComment):
    mentioned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='mentions'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Extract @mentions from comment text
        mentions = extract_mentions(self.comment)
        self.mentioned_users.set(mentions)
```
