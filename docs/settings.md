# Settings

Configure Django Tree Comments in your `settings.py`.

## Required Settings

### `INSTALLED_APPS`

Add `tree_comments` and required dependencies:

```python
INSTALLED_APPS = [
    ...
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'tree_comments',
]
```

### `SITE_ID`

Set the current site ID:

```python
SITE_ID = 1
```

## Comment Model Settings

### `TREE_COMMENTS_COMMENT_MODEL`

Custom comment model (default: `'tree_comments.Comment'`):

```python
TREE_COMMENTS_COMMENT_MODEL = 'myapp.CustomComment'
```

### `TREE_COMMENTS_COMMENT_FLAG_MODEL`

Custom comment flag model (default: `'tree_comments.CommentFlag'`):

```python
TREE_COMMENTS_COMMENT_FLAG_MODEL = 'myapp.CustomCommentFlag'
```

### `TREE_COMMENTS_COMMENT_FORM`

Custom comment form (default: `'tree_comments.forms.CommentForm'`):

```python
TREE_COMMENTS_COMMENT_FORM = 'myapp.forms.CustomCommentForm'
```

## Comment Settings

### `COMMENT_MAX_LENGTH`

Maximum comment length (default: `3000`):

```python
COMMENT_MAX_LENGTH = 3000
```

### `COMMENTS_TIMEOUT`

Time in seconds for comment preview timeout (default: `7200` = 2 hours):

```python
COMMENTS_TIMEOUT = 7200
```

### `COMMENTS_HIDE_REMOVED`

Hide removed comments from list (default: `True`):

```python
COMMENTS_HIDE_REMOVED = True
```

### `COMMENTS_ALLOW_PROFANITIES`

Allow profanities in comments (default: `False`):

```python
COMMENTS_ALLOW_PROFANITIES = False
```

## Profanity Filter

### `PROFANITIES_LIST`

Custom list of profane words:

```python
PROFANITIES_LIST = [
    'badword1',
    'badword2',
]
```
