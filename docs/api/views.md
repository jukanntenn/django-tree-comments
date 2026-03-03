# Views API

API reference for views in Django Tree Comments.

## Class-Based Views

### CommentPostView

Handle comment form submission.

**URL:** `/comments/post/`

**Methods:**
- `POST` - Submit a new comment

**Features:**
- Validates form data
- Creates comment
- Supports both HTML and JSON responses
- Handles threaded comments via `parent` field

**JSON Response:**

```json
{
    "comment": {
        "id": 1,
        "comment": "Great article!",
        "user_name": "John",
        "submit_date": "2026-03-03T10:00:00Z"
    }
}
```

### CommentListView

List comments for an object.

**URL:** `/comments/`

**Methods:**
- `GET` - Get comments for an object

**Query Parameters:**
- `content_type` - Content type ID
- `object_id` - Object primary key

**Features:**
- Returns comments as HTML or JSON
- Supports threaded comments

### CommentDetailView

Get details for a single comment.

**URL:** `/comments/<id>/`

**Methods:**
- `GET` - Get comment details

### ReplyView

Display reply form for a comment.

**URL:** `/comments/<id>/reply/`

**Methods:**
- `GET` - Display reply form

**Context:**
- `form` - Comment form with parent pre-filled
- `title` - "Reply to comment"

### FlagCommentView

Flag a comment for moderation.

**URL:** `/comments/<id>/flag/`

**Methods:**
- `GET` - Display flag confirmation
- `POST` - Flag the comment

**Requires:** Authenticated user

### DeleteCommentView

Delete a comment (moderator action).

**URL:** `/comments/<id>/delete/`

**Methods:**
- `GET` - Display delete confirmation
- `POST` - Delete the comment

**Requires:** Staff status

### ApproveCommentView

Approve a comment (moderator action).

**URL:** `/comments/<id>/approve/`

**Methods:**
- `GET` - Display approve confirmation
- `POST` - Approve the comment

**Requires:** Staff status

## Function-Based Views

### mute_csrf

Decorator that mutes CSRF for specific views.

**Usage:**

```python
from tree_comments.views import mute_csrf

@mute_csrf
def my_view(request):
    # CSRF exempt
    pass
```

## JSON API

All views support JSON responses when `Accept: application/json` header is present.

### Example

```javascript
fetch('/comments/post/', {
    method: 'POST',
    headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        content_type: 'blog.article',
        object_pk: '1',
        comment: 'Great article!'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Template Views

### CommentFormTemplateView

Render comment form for an object.

**URL:** `/comments/form/`

**Query Parameters:**
- `content_type` - Content type ID
- `object_id` - Object primary key

**Returns:** HTML form or JSON data

### CommentListTemplateView

Render comment list for an object.

**URL:** `/comments/list/`

**Query Parameters:**
- `content_type` - Content type ID
- `object_id` - Object primary key

**Returns:** HTML list or JSON data
