# Views API

API reference for the class-based views in Django Tree Comments.

All URLs are registered under the `tree_comments` URLconf; include it in your
project's `urlpatterns`:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("comments/", include("tree_comments.urls")),
]
```

## Views

### CommentPostView

Handle comment form submission.

| | |
|---|---|
| **URL name** | `tree-comments-post-comment` |
| **URL** | `post/` |
| **Methods** | `POST` |
| **Decorator** | `@csrf_protect` |

Validates form data, creates the comment (firing `comment_will_be_posted` /
`comment_was_posted` signals), and supports the `parent` field for threaded
replies. When the request carries `?format=html` the view returns an HTML
fragment (form-on-error / comment-on-success) instead of a redirect — useful
for HTMX-style partial rendering.

### CommentFormTemplateView

Render (or return as JSON) the comment form for a given object.

| | |
|---|---|
| **URL name** | `tree-comments-form` |
| **URL** | `form/` |
| **Query params** | `content_type`, `object_pk`, optional `parent` |

Returns `form.as_json()` as `application/json` when the `Accept` header
requests JSON, otherwise renders `tree_comments/form.html`. Passing `parent`
pre-fills the reply parent.

### ReplyView

Display the reply form for a specific comment.

| | |
|---|---|
| **URL name** | `tree-comments-reply` |
| **URL** | `<comment_id>/reply/` |
| **Methods** | `GET` |

Context includes `form` (with `parent` pre-filled) and `title`
("Reply to comment").

### FlagView

Flag a comment for moderator review.

| | |
|---|---|
| **URL name** | `tree-comments-flag` |
| **URL** | `flag/<comment_id>/` |
| **Methods** | `GET`, `POST` |
| **Requires** | Authenticated user |

Creates a `CommentFlag` with `SUGGEST_REMOVAL` and fires
`comment_was_flagged`.

### DeleteView

Remove a comment (moderator action).

| | |
|---|---|
| **URL name** | `tree-comments-delete` |
| **URL** | `delete/<comment_id>/` |
| **Methods** | `GET`, `POST` |
| **Requires** | `<app_label>.can_moderate` permission |

Sets `is_removed=True` and creates a `MODERATOR_DELETION` flag.

### ApproveView

Approve a comment from the moderation queue.

| | |
|---|---|
| **URL name** | `tree-comments-approve` |
| **URL** | `approve/<comment_id>/` |
| **Methods** | `GET`, `POST` |
| **Requires** | `<app_label>.can_moderate` permission |

Sets `is_public=True` / `is_removed=False` and creates a
`MODERATOR_APPROVAL` flag.

### Confirmation / done views

| View | URL name | Template |
|---|---|---|
| `CommentDoneView` | `tree-comments-comment-done` (`posted/`) | `tree_comments/posted.html` |
| `FlagDoneView` | `tree-comments-flag-done` (`flagged/`) | `tree_comments/flagged.html` |
| `DeleteDoneView` | `tree-comments-delete-done` (`deleted/`) | `tree_comments/deleted.html` |
| `ApproveDoneView` | `tree-comments-approve-done` (`approved/`) | `tree_comments/approved.html` |

### Content-object redirect

`tree-comments-url-redirect` (`cr/<content_type_id>/<object_pk>/`) redirects to
the commented object's absolute URL.

## Internal helpers

These are not part of the public API but are documented for completeness:

- `CommentPostBadRequest` — HTTP 400 response (renders `400-debug.html` when
  `DEBUG` is on).
- `BadRequest` — exception wrapping a `CommentPostBadRequest`, used internally
  by `resolve_comment_target`.
- `resolve_comment_target(ctype, object_pk, using=None)` — resolves
  `content_type` + `object_pk` to the target object, raising `BadRequest` on
  failure.
- `inject_comment_target` — decorator that injects the resolved target into
  `view.kwargs["target"]`.
- `CommentActionRedirectMixin`, `CommentModerationPermissionMixin` — CBV mixins
  shared by the moderation views.
