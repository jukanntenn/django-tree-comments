# django-tree-comments — custom comment model demo

A minimal Django project showing how to **swap the comment model** via
`TREE_COMMENTS_COMMENT_MODEL` while keeping the full modern UI. This project
uses `comments.Comment` (a trivial `AbstractComment` subclass) instead of the
bundled `tree_comments.Comment`, and demonstrates a **traditional (non-HTMX)**
comment flow.

It reuses the same Reddit/Disqus-class comment UI as the `default` demo
(avatars, reply-to relationships, quote bubbles, collapse, sort, relative
times), but submits comments via standard POST + redirect instead of HTMX —
proving the UI bundle is flow-agnostic.

For the full-featured demo (HTMX, faker seeding, multiple topologies),
see [`../default/`](../default/README.md).

## Run it

```bash
cd examples/custom
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser   # fixture references user pk=1
uv run python manage.py loaddata blog
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## How the swap works

1. `comments/models.py` defines `Comment(AbstractComment): pass`.
2. `custom/settings.py` sets `TREE_COMMENTS_COMMENT_MODEL = "comments.Comment"`.
3. The fixture under `blog/fixtures/blog.json` targets `comments.comment`.

That's it — every `get_comment_model()` call now returns `comments.Comment`,
and all manager methods (`threaded_for_instance`, `visible`, etc.) are inherited.

## How the UI is layered

Same extension points as the `default` demo:

- `custom/settings.py` adds `templates/` to `TEMPLATES["DIRS"]` so the project's
  `templates/tree_comments/*.html` override the package defaults.
- `blog/static/tree_comments/` holds the shared CSS/JS bundle.
- `blog/templatetags/blog_tags.py` → `build_nested_for_post` builds the nested
  tree using the **swapped** model (`get_comment_model()`).
- `blog/templates/blog/detail.html` composes the app with `get_comment_form` +
  the nested-tree filter + `include "tree_comments/app.html"` (no HTMX).
