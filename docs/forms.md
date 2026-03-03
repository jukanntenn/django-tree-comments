# Forms

Documentation for comment forms in Django Tree Comments.

## CommentForm

The main form for posting comments.

### Fields

- **`content_type`** - Hidden field for content type
- **`object_pk`** - Hidden field for object ID
- **`timestamp`** - Hidden field for security
- **`security_hash`** - Hidden field for security
- **`parent`** - Hidden field for threaded comments (optional)
- **`name`** - Name (for anonymous users)
- **`email`** - Email address
- **`url`** - Website URL (optional)
- **`comment`** - The comment text
- **`honeypot`** - Spam protection field

### Usage

#### Basic Form

```python
from tree_comments import get_comment_form

form_class = get_comment_form()
form = form_class(article)
```

#### Reply Form

```python
form = form_class(article, parent=parent_comment)
```

#### In Template

```django
<form action="{% url 'tree-comments-post-comment' %}" method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Post Comment</button>
</form>
```

## CommentDetailsForm

Extends CommentSecurityForm with comment details.

### Features

- Handles parent comment for threading
- Validates comment length
- Provides spam protection via honeypot

## Form Security

### Timestamp Validation

Forms expire after 2 hours (configurable via `COMMENTS_TIMEOUT`).

### Security Hash

Prevents form tampering by validating:

- Content type
- Object ID
- Timestamp

### Honeypot

Hidden field that should remain empty. Bots often fill it, triggering spam detection.

## Custom Forms

Create a custom form by extending CommentDetailsForm:

```python
from tree_comments.forms import CommentDetailsForm

class CustomCommentForm(CommentDetailsForm):
    def clean_comment(self):
        comment = self.cleaned_data['comment']
        # Add custom validation
        if 'spam' in comment.lower():
            raise forms.ValidationError("No spam allowed!")
        return comment
```

Configure in settings:

```python
TREE_COMMENTS_COMMENT_FORM = 'myapp.forms.CustomCommentForm'
```
