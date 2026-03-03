# Migration Guide

Guide for migrating from django-contrib-comments to django-tree-comments.

## Overview

Django Tree Comments is a modern fork of django-contrib-comments with:

- Threaded comment support
- Class-based views
- JSON API support
- CTE-based queries
- Modern Python packaging

## Key Differences

### Models

| Feature | django-contrib-comments | django-tree-comments |
|---------|------------------------|---------------------|
| Threaded support | No | Yes (`parent` field) |
| Manager methods | Basic | CTE-based tree queries |
| Model name | `Comment` | `Comment` (compatible) |

### Views

| Feature | django-contrib-comments | django-tree-comments |
|---------|------------------------|---------------------|
| View type | Function-based | Class-based |
| JSON API | No | Yes |
| URL names | `comments-*` | `tree-comments-*` |

### URL Names

All URL names changed from `comments-*` to `tree-comments-*`:

| Old | New |
|-----|-----|
| `comments-post-comment` | `tree-comments-post-comment` |
| `comments-flag` | `tree-comments-flag` |
| `comments-delete` | `tree-comments-delete` |
| `comments-approve` | `tree-comments-approve` |

## Migration Steps

### 1. Install Package

```bash
pip uninstall django-contrib-comments
pip install django-tree-comments
```

### 2. Update Settings

```python
INSTALLED_APPS = [
    # Remove 'django_comments'
    # Add 'tree_comments'
    'tree_comments',
]
```

### 3. Update URL Patterns

```python
# Old
urlpatterns = [
    path('comments/', include('django_comments.urls')),
]

# New
urlpatterns = [
    path('comments/', include('tree_comments.urls')),
]
```

### 4. Update Template Tags

```django
<!-- Old -->
{% load comments %}

<!-- New -->
{% load tree_comments %}
```

### 5. Update Template Code

Update URL names in templates:

```django
<!-- Old -->
<a href="{% url 'comments-flag' comment.id %}">Flag</a>

<!-- New -->
<a href="{% url 'tree-comments-flag' comment.id %}">Flag</a>
```

### 6. Run Migrations

```bash
python manage.py migrate tree_comments
```

The existing `Comment` table will be preserved. Django Tree Comments uses the same table structure with an additional `parent` column.

### 7. Add Parent Column

Django Tree Comments will add a `parent` column to your existing comments table:

```sql
ALTER TABLE django_comments ADD COLUMN parent_id INTEGER NULL;
```

## Using New Features

### Threaded Comments

Now you can create threaded comments:

```python
# Create a reply
reply = Comment.objects.create(
    content_object=article,
    parent=original_comment,
    comment="This is a reply",
    user=request.user
)
```

### CTE Queries

Use the new CTE-based manager:

```python
# Get threaded comments with level information
comments = Comment.objects.cte_for_instance(article)
for comment in comments:
    print(f"{'  ' * comment.level}{comment.comment}")
```

### JSON API

Use the JSON API for AJAX:

```javascript
fetch('/comments/', {
    headers: {'Accept': 'application/json'}
})
.then(r => r.json())
.then(data => console.log(data));
```

## Custom Models

If you have a custom comment model:

1. Change base class from `django_comments.models.AbstractComment` to `tree_comments.models.AbstractComment`
2. Update `TREE_COMMENTS_COMMENT_MODEL` setting (was `COMMENTS_COMMENT_MODEL`)

## Signals

Signal names remain the same:

- `comment_will_be_posted`
- `comment_was_posted`
- `comment_was_flagged`

Import from new location:

```python
# Old
from django_comments.signals import comment_was_posted

# New
from tree_comments.signals import comment_was_posted
```

## Troubleshooting

### Template Syntax Errors

Make sure to update all `{% load comments %}` to `{% load tree_comments %}`.

### URL Resolution Errors

Update all URL names from `comments-*` to `tree-comments-*`.

### Missing Parent Column

If migrations don't run automatically:

```bash
python manage.py makemigrations tree_comments
python manage.py migrate tree_comments
```

## Rollback

To rollback to django-contrib-comments:

1. Uninstall django-tree-comments
2. Reinstall django-contrib-comments
3. Update INSTALLED_APPS
4. Update template tags and URL names

The `parent` column will remain but won't be used.
