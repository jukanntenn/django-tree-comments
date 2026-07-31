# django-tree-comments

A Django app for threaded (nested) comments using Common Table Expressions
(CTE), ported and extended from
[django-contrib-comments](https://github.com/django/django-contrib-comments).

> This library is under active development. Version numbers follow the `0.0.x`
> scheme during the experimental stage; SemVer rules will apply once `1.0.0` is
> reached.

## Features

- **Threaded comments** — a self-referential `parent` foreign key models the
  reply tree (adjacency list, zero redundant tree columns).
- **CTE tree queries** — recursive Common Table Expressions fetch an entire
  comment tree in a single query, with `depth` and `root_id` annotations.
- **Multi-backend** — works on PostgreSQL, MySQL, and SQLite.
- **Swappable models & forms** — customize `Comment`, `CommentFlag`, and the
  form class via `TREE_COMMENTS_COMMENT_MODEL`,
  `TREE_COMMENTS_COMMENT_FLAG_MODEL`, and `TREE_COMMENTS_COMMENT_FORM`.
- **Class-based views with JSON / HTML-fragment responses** — friendly to
  AJAX and HTMX-style partial rendering.
- **Moderation, flagging, RSS feeds, Django admin integration** — full feature
  parity with django-contrib-comments.
- **Internationalization** — ships `.po` catalogs for 70+ languages.

## Requirements

- Python 3.10+
- Django 5.2+
- [django-cte](https://github.com/dimagi/django-cte)

## Installation

```bash
pip install django-tree-comments
```

Add `tree_comments` and `django.contrib.sites` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.sites",
    "tree_comments",
]
```

Run the migrations:

```bash
python manage.py migrate
```

## Quick start

Render a whole threaded comment app (list + reply form) for any object with a
single template tag:

```django
{% load tree_comments %}

{% render_comment_app for article %}
```

Each comment in the tree carries an annotated `depth` (and `root_id`), so
templates can indent replies without extra queries:

```django
<div class="comment{% if comment.depth %} is-child{% endif %}">
    {{ comment.comment }}
    <a href="{{ comment.get_reply_url }}">Reply</a>
</div>
```

See the [Quick Start guide](https://django-tree-comments.readthedocs.io) for the
full walkthrough.

## Example projects

Two runnable example projects live under [`examples/`](examples):

- [`examples/default`](examples/default) — the default `tree_comments.Comment`
  model.
- [`examples/custom`](examples/custom) — a custom swappable comment model and
  templates.

## Documentation

Full documentation is at
[django-tree-comments.readthedocs.io](https://django-tree-comments.readthedocs.io),
including:

- [Settings](https://django-tree-comments.readthedocs.io) — configuration
  options (`TREE_COMMENTS_*` settings).
- [Models](https://django-tree-comments.readthedocs.io) — the `parent` field,
  CTE query methods (`cte_for_instance`, `threaded_for_instance`).
- [Custom apps](https://django-tree-comments.readthedocs.io) — swappable models
  & forms.

## License

BSD-3-Clause, see [LICENSE](LICENSE).
