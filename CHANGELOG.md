# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.4rc1] - 2026-07-28

First release candidate: threaded comments via recursive CTE queries,
ported and extended from django-contrib-comments.

### Added

- **Threaded comments** — reply to any comment with a `parent` field; the entire
  tree (including reply depth) is fetched in a single query via recursive Common
  Table Expressions.
- **Swappable models and form** — customize the `Comment` model, `CommentFlag`
  model, and the comment form through `TREE_COMMENTS_COMMENT_MODEL`,
  `TREE_COMMENTS_COMMENT_FLAG_MODEL`, and `TREE_COMMENTS_COMMENT_FORM` settings.
- **HTMX-friendly responses** — comment-post, flag, delete, and approve views
  return HTML fragments so the page updates without a full reload.
- **JSON API** — request the comment form and lists as JSON for AJAX clients.
- **Single-tag rendering** — `{% render_comment_app for object %}` renders a
  complete threaded comment section (list + reply form) in one template tag.
- **Built-in moderation** — flagging, removal, and approval workflows with
  Django admin integration.
- **RSS/Atom feeds** for comments on any content object.
- **Internationalization** — ships translation catalogs for 70+ languages.

### Changed

- Requires **Django 5.2+** and **Python 3.10+**.
- Settings use the modern `TREE_COMMENTS_*` swappable-model pattern instead of
  the legacy `COMMENTS_APP` mechanism.

### Removed

- The legacy `COMMENTS_APP` pluggable-app mechanism is no longer supported.

[Unreleased]: https://github.com/jukanntenn/django-tree-comments/compare/v0.0.4rc1...HEAD
[0.0.4rc1]: https://github.com/jukanntenn/django-tree-comments/releases/tag/v0.0.4rc1
