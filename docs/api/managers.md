# Managers API

API reference for the comment queryset and manager in Django Tree Comments.

## Overview

`CommentManager` is built via
[`Manager.from_queryset(CommentQuerySet)`](https://docs.djangoproject.com/en/stable/topics/db/managers/#from-queryset),
so every queryset method is also available directly on the manager
(`Comment.objects.visible()`, `Comment.objects.for_model(...)`, …).

All tree-traversal methods are powered by
[django-cte](https://github.com/dimagi/django-cte) recursive Common Table
Expressions and work on **PostgreSQL, MySQL, and SQLite**.

## QuerySet / Manager methods

### `visible()`

Return only comments that are both public and not removed.

```python
Comment.objects.visible()
# equivalent: Comment.objects.filter(is_public=True, is_removed=False)
```

### `roots()`

Return only visible, top-level (parent-less) comments.

### `in_moderation()`

Return comments waiting in the moderation queue (not public, not removed).

### `for_model(model)`

Return all comments for a model class or instance.

```python
Comment.objects.for_model(Article)  # all comments on any Article
Comment.objects.for_model(article)  # comments on one article instance
```

### `cte_for_instance(instance)`

Fetch the **entire comment tree** for `instance` in a single recursive CTE
query. Each comment is annotated with:

- `depth` — nesting level (`0` for root comments)
- `root_id` — the id of the top-level ancestor

```python
from tree_comments.models import Comment

comments = Comment.objects.cte_for_instance(article)
for comment in comments:
    print(f"{'  ' * comment.depth}{comment.comment}")
```

### `threaded_for_instance(instance)`

Like `cte_for_instance`, but the result is ordered for threaded display
(by descending `root_id`, then `submit_date`, then `id`) and uses
`select_related("parent", "user", "content_type")` so rendering the tree
in a template does not trigger N+1 queries.

```python
comments = Comment.objects.threaded_for_instance(article)
```

## Usage

### Accessing the manager

```python
from tree_comments import get_comment_model

Comment = get_comment_model()
comments = Comment.objects.threaded_for_instance(article)
```

### Custom manager

Because `CommentManager` is `from_queryset`-based, extend `CommentQuerySet`
and generate a new manager:

```python
from django.db import models
from tree_comments.managers import CommentQuerySet


class CommentQuerySet(CommentQuerySet):
    def recent(self, days=7):
        from datetime import timedelta
        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(submit_date__gte=cutoff)


CommentManager = models.Manager.from_queryset(CommentQuerySet)
```

## Performance

The recursive CTE fetches the whole tree in **one query**. Because
`threaded_for_instance` already calls `select_related("parent", "user",
"content_type")`, accessing those relations in a template does not add extra
queries. You can chain additional `select_related` / `prefetch_related`:

```python
comments = Comment.objects.cte_for_instance(article).select_related("user")
```
