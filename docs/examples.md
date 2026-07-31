# Examples

!!! tip "Runnable examples"
    Two complete Django projects live under [`examples/`](https://github.com/jukanntenn/django-tree-comments/tree/main/examples)
    in the repository:

    - **[`examples/default`](https://github.com/jukanntenn/django-tree-comments/tree/main/examples/default)**
      — the full demo: 5 posts with different comment topologies, faker-seeded
      data via `seed_comments`, and an HTMX-powered threaded UI. Start here.
    - **[`examples/custom`](https://github.com/jukanntenn/django-tree-comments/tree/main/examples/custom)**
      — a minimal demo of swapping the comment model via
      `TREE_COMMENTS_COMMENT_MODEL`.

    Each has its own README with run instructions.

---

Real-world examples of using Django Tree Comments.

## Basic Blog Comments

### Model

```python
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    published = models.BooleanField(default=False)
```

### Template

```django
{% load tree_comments %}

<article>
    <h1>{{ article.title }}</h1>
    <div>{{ article.body }}</div>
</article>

<section class="comments">
    <h2>Comments</h2>
    {% render_comment_list for article %}
    {% render_comment_form for article %}
</section>
```

## Threaded Comments with Indentation

### Template

```django
{% load tree_comments %}

{% get_comment_list for article as comment_list %}
<div class="comment-tree">
    {% for comment in comment_list %}
        <div class="comment" style="margin-left: {{ comment.depth }}em;">
            <p>{{ comment.comment }}</p>
            <small>By {{ comment.user_name }} on {{ comment.submit_date }}</small>
            <a href="{{ comment.get_reply_url }}">
                Reply
            </a>
        </div>
    {% endfor %}
</div>
```

## AJAX Comment Submission

### JavaScript

```javascript
async function submitComment(form) {
    const formData = new FormData(form);

    const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json'
        }
    });

    if (response.ok) {
        const data = await response.json();
        // Update UI with new comment
        addCommentToDOM(data);
    }
}
```

### View

The built-in views automatically handle JSON requests when `Accept: application/json` header is present.

## Custom Comment Model

### models.py

```python
from tree_comments.models import AbstractComment


class Review(AbstractComment):
    rating = models.IntegerField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)

    class Meta(AbstractComment.Meta):
        abstract = False
```

### settings.py

```python
TREE_COMMENTS_COMMENT_MODEL = "reviews.Review"
```

## Email Notifications

### signals.py

```python
from django.core.mail import send_mail
from django.conf import settings
from tree_comments.signals import comment_was_posted


def notify_author(sender, comment, request, **kwargs):
    author = comment.content_object.author
    subject = f"New comment on {comment.content_object}"
    message = f"{comment.user_name} commented: {comment.comment}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [author.email])


comment_was_posted.connect(notify_author)
```

## Comment Moderation

### moderation.py

```python
from tree_comments.moderation import CommentModerator, moderator


class ArticleModerator(CommentModerator):
    email_notification = True
    auto_moderate_field = "published"
    moderate_after = 0  # Moderate all comments


moderator.register(Article, ArticleModerator)
```

## REST API Integration

### serializers.py

```python
from rest_framework import serializers
from tree_comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "user", "comment", "parent", "submit_date"]
        read_only_fields = ["user", "submit_date"]
```

### views.py

```python
from rest_framework import viewsets
from tree_comments.models import Comment


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        content_type_id = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")
        return Comment.objects.filter(content_type_id=content_type_id, object_pk=object_id)
```
