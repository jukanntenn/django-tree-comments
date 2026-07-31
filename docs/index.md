# Django Tree Comments

A Django app for threaded comments using Common Table Expressions (CTE).

## Features

- **Threaded Comments**: Hierarchical comment structure with parent-child relationships
- **CTE Queries**: Efficient tree queries using recursive Common Table Expressions (PostgreSQL, MySQL, and SQLite)
- **Modern Architecture**: Class-based views with JSON API support
- **Swappable Models**: Flexible model customization via settings
- **Django Admin Integration**: Full admin interface for comment management
- **Moderation System**: Built-in comment moderation and flagging
- **RSS/Atom Feeds**: Comment feeds for content objects
- **Internationalization**: 70+ language translations

## Quick Links

- [Quick Start Guide](quickstart.md) - Get started in 5 minutes
- [Settings](settings.md) - Configuration options
- [Models](models.md) - Comment model documentation
- [Architecture](architecture.md) - Design philosophy and CTE queries

## Requirements

- Python 3.10+
- Django 5.2+
- PostgreSQL, MySQL, or SQLite

## Installation

```bash
pip install django-tree-comments
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'tree_comments',
]
```

## Comparison with django-contrib-comments

Django Tree Comments extends django-contrib-comments with:

- Threaded comment support via `parent` field
- CTE-based efficient tree queries
- Class-based views (CBV) instead of function-based views
- Built-in JSON API support for AJAX requests
- Modern Python packaging with pyproject.toml

See the [Migration Guide](migration.md) for details on moving from
django-contrib-comments.

## License

BSD-3-Clause
