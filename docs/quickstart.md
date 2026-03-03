# Quick Start Guide

Get started with Django Tree Comments in 5 minutes.

## Installation

Install the package:

```bash
pip install django-tree-comments
```

Add to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'tree_comments',
    'django.contrib.contenttypes',
    'django.contrib.sites',
]
```

Run migrations:

```bash
python manage.py migrate
```

## Basic Usage

### Display Comments

Load the template tags in your template:

```django
{% load tree_comments %}

<h2>Comments</h2>
{% render_comment_list for object %}
```

### Display Comment Form

Add a comment form:

```django
{% render_comment_form for object %}
```

### Threaded Comments

Display threaded comments with parent-child relationships:

```django
{% get_comment_list for object as comment_list %}
{% for comment in comment_list %}
    <div class="comment" style="margin-left: {{ comment.level }}em;">
        {{ comment.comment }}
        <a href="{{ comment.get_reply_url }}">Reply</a>
    </div>
{% endfor %}
```

### JSON API

Get comments as JSON for AJAX:

```python
import requests

response = requests.get(
    '/comments/form/',
    headers={'Accept': 'application/json'},
    params={'content_type': 'blog.article', 'object_id': 1}
)
data = response.json()
```

## Next Steps

- Read the [Settings](settings.md) documentation
- Learn about [Models](models.md) and query methods
- See [Examples](examples.md) for more use cases
