# Architecture

Design philosophy and technical architecture of Django Tree Comments.

## Design Goals

1. **Threaded Comments** - Support hierarchical comment structures
2. **Performance** - Efficient tree queries using CTE
3. **Modern Django** - Class-based views and best practices
4. **API-First** - Built-in JSON API support
5. **Extensibility** - Swappable models and forms

## Core Components

### Models

#### AbstractComment

Base model for comments with:

- Generic foreign key to any content object
- User information (authenticated or anonymous)
- Tree structure via `parent` field
- Moderation flags (`is_public`, `is_removed`)

#### AbstractCommentFlag

Base model for comment flags with:

- User who flagged
- Flag type
- Creation timestamp

### Managers

#### CommentManager

Custom manager with CTE-based queries:

```python
def cte_for_instance(self, object):
    """
    Get comments using Common Table Expression.

    Returns comments with 'depth' annotation for tree depth
    and 'root_id' for the top-level ancestor.
    Uses WITH RECURSIVE for efficient tree traversal.
    """
```

**SQL (simplified):**

```sql
WITH RECURSIVE tree AS (
    -- Base case: root comments
    SELECT id, parent_id, comment, id AS root_id, 0 AS depth
    FROM tree_comments_comment
    WHERE object_pk = %s AND parent_id IS NULL

    UNION ALL

    -- Recursive case: child comments
    SELECT c.id, c.parent_id, c.comment, tree.root_id, tree.depth + 1
    FROM tree_comments_comment c
    INNER JOIN tree ON c.parent_id = tree.id
)
SELECT * FROM tree;
```

> The recursive CTE works on **PostgreSQL, MySQL, and SQLite** (all support
> `WITH RECURSIVE`).

### Views

#### Class-Based Architecture

All views are class-based for better extensibility:

```python
class CommentPostView(View):
    def post(self, request):
        # Handle comment submission

    def get(self, request):
        # Return form or JSON
```

#### JSON API Support

Views check `Accept` header and return JSON when appropriate:

```python
def dispatch(self, request, *args, **kwargs):
    if request.headers.get("Accept") == "application/json":
        return self.json_response()
    return super().dispatch(request, *args, **kwargs)
```

### Forms

#### CommentSecurityForm

Handles anti-spoofing:

- Timestamp validation (prevents replay attacks)
- Security hash (prevents tampering)
- Honeypot field (spam protection)

#### CommentDetailsForm

Extends security form with:

- Comment content
- Parent field for threading
- User information

## Tree Structure

### Database Schema

```sql
CREATE TABLE tree_comments_comment (
    id SERIAL PRIMARY KEY,
    content_type_id INTEGER,
    object_pk VARCHAR(64),
    site_id INTEGER,
    user_id INTEGER,
    user_name VARCHAR(50),
    user_email VARCHAR(254),
    user_url VARCHAR(200),
    comment TEXT,
    submit_date TIMESTAMP,
    ip_address INET,
    is_public BOOLEAN,
    is_removed BOOLEAN,
    parent_id INTEGER REFERENCES tree_comments_comment(id)
);
```

### Tree Traversal

Using CTE for efficient tree queries:

1. **Root Comments** - Comments with `parent_id = NULL`
2. **Child Comments** - Comments with `parent_id` set
3. **Depth Calculation** - Computed during CTE traversal (annotated as `depth`)

### Performance

**Single Query:**
- Entire tree loaded in one query
- No N+1 query problem
- Level information included

**Indexing:**
- Index on `(content_type_id, object_pk)` for object lookup
- Index on `parent_id` for tree traversal
- Index on `submit_date` for ordering

## URL Patterns

RESTful URL structure:

```
/comments/                    # List comments
/comments/post/               # Post new comment
/comments/<id>/               # Comment detail
/comments/<id>/reply/         # Reply to comment
/comments/<id>/flag/          # Flag comment
/comments/<id>/delete/        # Delete comment
/comments/<id>/approve/       # Approve comment
/comments/form/               # Get form HTML/JSON
/comments/list/               # Get list HTML/JSON
```

## Template Tags

### render_comment_list

Renders comment list template:

```django
{% render_comment_list for object %}
```

### render_comment_form

Renders comment form:

```django
{% render_comment_form for object %}
```

### get_comment_list

Gets comments as template variable:

```django
{% get_comment_list for object as comments %}
{% for comment in comments %}
    {{ comment.comment }}
{% endfor %}
```

## Signals

### Signal Flow

```
User submits form
    ↓
comment_will_be_posted
    ↓
Validate & Save
    ↓
comment_was_posted
    ↓
Redirect user
```

### Use Cases

- **Validation** - Use `comment_will_be_posted` for custom validation
- **Notifications** - Use `comment_was_posted` for email notifications
- **Spam Detection** - Use `comment_will_be_posted` for spam filtering

## Swappable Models

### Implementation

Uses Django's app registry:

```python
def get_comment_model():
    setting = getattr(settings, "TREE_COMMENTS_COMMENT_MODEL", "tree_comments.Comment")
    return apps.get_model(setting)
```

### Benefits

- Customize without forking
- Add custom fields
- Override methods
- Change managers

## Backwards Compatibility

### django-contrib-comments Compatibility

- Same model fields (plus `parent`)
- Same signals
- Same template tags (different namespace)
- Same moderation system

### Migration Path

1. Install django-tree-comments
2. Update imports
3. Run migrations
4. Use new features (threading, JSON API)

## Future Enhancements

- **Django REST Framework** integration
- **GraphQL** support
- **Real-time** comments with WebSockets
- **Reactions** (like, love, etc.)
- **Mentions** (@username)
- **Markdown** support
