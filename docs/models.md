# Models

Documentation for the Comment model and its tree-specific features.

## Comment Model

The `Comment` model represents a user comment with threaded support.

### Fields

#### Tree-Specific Fields

- **`parent`** - ForeignKey to self for threaded comments
  - Nullable, allows building comment trees
  - `verbose_name`: "parent comment"
  - `help_text`: "The parent comment being replied to"

#### Standard Fields

- **`content_type`** - ForeignKey to ContentType
- **`object_pk`** - Primary key of the related object
- **`content_object`** - GenericForeignKey for easy access
- **`site`** - ForeignKey to Site
- **`user`** - ForeignKey to User (nullable for anonymous comments)
- **`user_name`** - Name for anonymous users
- **`user_email`** - Email for anonymous users
- **`user_url`** - URL for anonymous users
- **`comment`** - The comment text (max 3000 characters)
- **`submit_date`** - When the comment was submitted
- **`ip_address`** - IP address of the commenter
- **`is_public`** - Whether the comment is visible
- **`is_removed`** - Whether the comment has been removed

### Methods

#### Tree Methods

- **`get_reply_url()`** - Get URL to reply to this comment

#### Standard Methods

- **`__str__()`** - String representation
- **`save()`** - Auto-populate submit_date
- **`get_content_object_url()`** - Get URL for the related object

## CommentFlag Model

Flags for reporting inappropriate comments.

### Fields

- **`user`** - User who flagged the comment
- **`comment`** - The flagged comment
- **`flag`** - Flag type (suggest, remove, etc.)
- **`flag_date`** - When the comment was flagged

## Managers

### CommentManager

Custom manager with tree-specific query methods.

#### Methods

- **`cte_for_instance(object)`** - Get all comments for an object using CTE
- **`in_moderation()`** - Get comments awaiting moderation
- **`for_model(model)`** - Get comments for a specific model class

## Usage Examples

### Creating a Threaded Comment

```python
from tree_comments.models import Comment

# Create a root comment
root = Comment.objects.create(content_object=article, user=request.user, comment="Great article!")

# Create a reply
reply = Comment.objects.create(
    content_object=article, user=request.user, parent=root, comment="I agree with this comment"
)
```

### Querying Threaded Comments

```python
# Get all comments for an article as a tree (single CTE query)
comments = Comment.objects.cte_for_instance(article)

# Each comment is annotated with:
#   depth   - nesting level (0 for roots)
#   root_id - id of the top-level ancestor
for comment in comments:
    print("  " * comment.depth + comment.comment)
```

#### `threaded_for_instance(instance)`

Like `cte_for_instance`, but ordered for threaded display and with
`select_related("parent", "user", "content_type")` applied so templates can
render the tree without N+1 queries:

```python
comments = Comment.objects.threaded_for_instance(article)
```

#### `roots()`

Return only visible top-level comments (no parent):

```python
top_level = Comment.objects.for_model(article).roots()
```

#### `visible()`

Return only public, non-removed comments:

```python
Comment.objects.visible()
```
