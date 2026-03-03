# Managers API

API reference for custom managers in Django Tree Comments.

## CommentManager

The `CommentManager` provides methods for querying comments.

### Methods

#### `cte_for_instance(object)`

Get all comments for an object using Common Table Expressions for efficient tree queries.

**Parameters:**
- `object` - The object to get comments for

**Returns:**
- QuerySet of comments with `level` annotation for tree depth

**Example:**

```python
from tree_comments.models import Comment

comments = Comment.objects.cte_for_instance(article)
for comment in comments:
    print(f"{'  ' * comment.level}{comment.comment}")
```

#### `in_moderation()`

Get comments that are awaiting moderation.

**Returns:**
- QuerySet of non-public comments

**Example:**

```python
pending = Comment.objects.in_moderation()
```

#### `for_model(model)`

Get all comments for a specific model class.

**Parameters:**
- `model` - Model class or instance

**Returns:**
- QuerySet of comments

**Example:**

```python
from myapp.models import Article

comments = Comment.objects.for_model(Article)
```

## Usage

### Accessing the Manager

```python
from tree_comments import get_comment_model

Comment = get_comment_model()
comments = Comment.objects.cte_for_instance(article)
```

### Custom Manager

Create a custom manager by extending CommentManager:

```python
from tree_comments.managers import CommentManager as BaseManager

class CustomManager(BaseManager):
    def approved(self):
        return self.filter(is_public=True, is_removed=False)

    def recent(self, days=7):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(submit_date__gte=cutoff)
```

## Performance

### CTE Queries

The `cte_for_instance` method uses PostgreSQL CTE for efficient tree traversal:

- Single query for entire comment tree
- Includes `level` annotation for depth
- Ordered by tree structure

### Query Optimization

Use `select_related` and `prefetch_related` for better performance:

```python
comments = Comment.objects.cte_for_instance(article).select_related('user')
```
