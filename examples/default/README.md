# django-tree-comments — main demo

A runnable Django project demonstrating django-tree-comments with a
**Reddit/Disqus-class comment experience** built entirely through the package's
extension mechanisms (template overrides + static assets), without touching the
base package.

## Features

- **5 posts**, each with a different comment topology (wide-shallow, flat-replies, wide-deep, empty, deep-chain).
- **faker-seeded** comment data via a `seed_comments` management command.
- **HTMX-powered** threaded UI: post comments, reply inline, and soft-delete without page reloads.
- **Letter avatars** — each commenter gets a colored circle with their initial; the color is deterministic (same name → same color, Disqus-style).
- **"reply to @name"** relationship — replies show who they reply to, with a click-to-jump link that scrolls to and highlights the parent comment.
- **Quote bubbles** — the parent comment's excerpt is shown above a reply (hover context).
- **Collapsible subtrees** — collapse/expand any thread; deep chains auto-collapse past depth 6.
- **"Show N more replies"** — flat reply lists virtualize to keep long threads scannable.
- **Sort** newest/oldest (client-side, no round-trip).
- **Relative timestamps** ("2 hours ago") rendered client-side.
- **Live char counter** on the composer, aware of `COMMENT_MAX_LENGTH`.
- **Empty state** with an inviting call-to-action card.
- **Light + dark themes** (follows `prefers-color-scheme`), fully responsive down to mobile.

## Requirements

- Python ≥ 3.10
- Django ≥ 4.2
- (managed via [uv](https://docs.astral.sh/uv/))

## Run it

```bash
cd examples/default
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser   # required: seed needs ≥1 user for post.author
uv run python manage.py seed_comments
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

## What you'll see

| Post | Topology | Description |
|------|----------|-------------|
| Welcome to django-tree-comments demo | wide-shallow | ~60 roots, 1-3 replies each |
| Ask Me Anything | flat-replies | 10 roots, ~15 replies each |
| Technical deep dive | wide-deep | 40 roots spawning balanced sub-trees |
| Empty comments section | empty | empty-state UI |
| A long back-and-forth discussion | deep-chain | single 9-11 level reply chain |

## seed_comments options

```bash
uv run python manage.py seed_comments              # default seed=42, flush existing comments
uv run python manage.py seed_comments --seed 7     # different random data
uv run python manage.py seed_comments --no-flush   # append instead of flush
uv run python manage.py seed_comments -v 2         # verbose progress
```

## Re-running

`seed_comments` is idempotent for posts/users (get-or-create by title/username) but **clears all comments** by default. Superusers are never touched.

## How the UI is layered (extension points)

This demo does **not** modify the base package. Everything is composed from the
extension points the package exposes:

- **Template overrides** in `templates/tree_comments/{app,comment,form,reply}.html`
  — Django's `APP_DIRS` loader finds these project templates before the package
  defaults. This is where the avatars, reply-to links, quote bubbles, actions,
  and the composer live.
- **Static asset bundle** in `blog/static/tree_comments/`:
  - `css/tokens.css` — design tokens (palette, spacing, typography, light/dark).
  - `css/comments.css` — component styles (avatars, thread guides, collapse, forms).
  - `css/markdown.css` — comment-body prose styles.
  - `js/comments.js` — progressive enhancement (avatar painting, relative time,
    sort, collapse, "show more replies", anchor highlight). Zero dependencies.
- **HTMX** is loaded from a CDN in `blog/templates/blog/base.html`; the comment
  forms/replies use `hx-post`/`hx-get`/`hx-target`/`hx-swap` for no-reload UX.
- **A templatetag** (`blog/templatetags/blog_tags.py` → `build_nested_for_post`)
  converts the flat CTE result into a nested tree for recursive rendering.

## Files of interest

- `blog/management/commands/seed_comments.py` — the seeder.
- `blog/topology.py` — comment-tree topology generator.
- `blog/sentences.py` — theme-based sentence pools (no lorem ipsum).
- `blog/tree_utils.py` — flat-CTE → nested-tree converter.
- `blog/templatetags/blog_tags.py` — `build_nested_for_post` filter.
- `templates/tree_comments/*.html` — HTMX-enabled template overrides (the UI).
- `blog/static/tree_comments/` — the CSS/JS asset bundle.
- `blog/static/blog/style.css` — page-level chrome only (header, post, list).
- `blog/views.py` — `htmx_delete_comment` endpoint for soft-delete.
