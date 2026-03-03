# Django-Tree-Comments Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate missing features from django-contrib-comments to django-tree-comments including API functions, i18n, documentation, CI/CD, and tests.

**Architecture:** Add three URL helper functions, migrate 70+ language translations with tree-specific strings, convert Sphinx docs to MkDocs Markdown, setup tox+GitHub Actions with uv plugin, modernize pyproject.toml, and add comprehensive API tests.

**Tech Stack:** Python 3.8+, Django 4.2+, pytest, tox, uv, MkDocs, GitHub Actions

---

## Phase 1: Core API Functions

### Task 1: Add Missing URL Helper Functions

**Files:**
- Modify: `tree_comments/__init__.py`

**Step 1: Add get_flag_url function**

Add to `tree_comments/__init__.py` after `get_comment_form_target()`:

```python
def get_flag_url(comment):
    """
    Get the URL for the "flag this comment" view.
    """
    return reverse("tree-comments-flag", args=(comment.id,))
```

**Step 2: Add get_delete_url function**

Add to `tree_comments/__init__.py` after `get_flag_url()`:

```python
def get_delete_url(comment):
    """
    Get the URL for the "delete this comment" view.
    """
    return reverse("tree-comments-delete", args=(comment.id,))
```

**Step 3: Add get_approve_url function**

Add to `tree_comments/__init__.py` after `get_delete_url()`:

```python
def get_approve_url(comment):
    """
    Get the URL for the "approve this comment from moderation" view.
    """
    return reverse("tree-comments-approve", args=(comment.id,))
```

**Step 4: Commit**

```bash
git add tree_comments/__init__.py
git commit -m "feat: add get_flag_url, get_delete_url, and get_approve_url API functions"
```

---

### Task 2: Update pyproject.toml with Comprehensive Metadata

**Files:**
- Modify: `pyproject.toml`

**Step 1: Update project metadata section**

Replace the `[project]` section in `pyproject.toml`:

```toml
[project]
name = "django-tree-comments"
version = "0.0.5"
description = "A Django app for threaded comments using Common Table Expressions (CTE)"
readme = "README.md"
license = "BSD-3-Clause"
license-files = ["LICENSE"]
requires-python = ">=3.8"
authors = [
    { name = "jukanntenn", email = "jukanntenn@outlook.com" }
]
maintainers = [
    { name = "jukanntenn", email = "jukanntenn@outlook.com" }
]
keywords = [
    "django",
    "comments",
    "threaded",
    "tree",
    "cte",
    "nested",
    "replies"
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Framework :: Django",
    "Framework :: Django :: 4.2",
    "Framework :: Django :: 5.0",
    "Framework :: Django :: 5.1",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
]
dependencies = [
    "django>=4.2",
    "django-cte>=1.3.3",
]
```

**Step 2: Add optional dependencies section**

Add after the `[project]` section:

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-django>=4.5",
    "pytest-cov>=4.0",
]
dev = [
    "django-tree-comments[test]",
    "ruff>=0.1.0",
    "djlint>=1.7.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "pymdown-extensions>=10.0.0",
]
```

**Step 3: Add project URLs section**

Add after `[project.optional-dependencies]`:

```toml
[project.urls]
Homepage = "https://github.com/jukanntenn/django-tree-comments"
Documentation = "https://django-tree-comments.readthedocs.io"
Repository = "https://github.com/jukanntenn/django-tree-comments"
Changelog = "https://github.com/jukanntenn/django-tree-comments/blob/main/CHANGELOG.md"
Issues = "https://github.com/jukanntenn/django-tree-comments/issues"
```

**Step 4: Remove old dependency-groups section**

Delete the `[dependency-groups]` section (lines 15-17).

**Step 5: Update pytest configuration**

Replace the `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.settings"
python_files = "tests.py test_*.py"
addopts = "-v --tb=short"
```

**Step 6: Add coverage configuration**

Add after `[tool.ruff]` section:

```toml
[tool.coverage.run]
source = ["tree_comments"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

**Step 7: Commit**

```bash
git add pyproject.toml
git commit -m "feat: modernize pyproject.toml with comprehensive metadata

- Update Python requirement to >=3.8
- Add explicit Django>=4.2 dependency
- Add comprehensive PyPI classifiers
- Organize dependencies into test/dev/docs extras
- Add project URLs for documentation, changelog, issues
- Add coverage configuration"
```

---

## Phase 2: Testing

### Task 3: Add Comment Fixture to conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Read existing conftest.py**

Read: `tests/conftest.py`

**Step 2: Add comment fixture**

Add at the end of `tests/conftest.py`:

```python
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from tree_comments.models import Comment
from tests.app.models import Article


@pytest.fixture
def article(db):
    """Create a test article for comments."""
    return Article.objects.create(title="Test Article")


@pytest.fixture
def comment(db, article):
    """Create a test comment."""
    return Comment.objects.create(
        comment="Test comment content",
        content_object=article,
        site=Site.objects.get_current(),
    )
```

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add article and comment fixtures for API tests"
```

---

### Task 4: Create test_app_api.py for API Functions

**Files:**
- Create: `tests/test_app_api.py`

**Step 1: Write test file header and imports**

Create `tests/test_app_api.py`:

```python
"""
Tests for the public API functions and swappable model support.
"""
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from tree_comments import (
    get_comment_model,
    get_comment_flag_model,
    get_comment_form,
    get_comment_form_target,
    get_flag_url,
    get_delete_url,
    get_approve_url,
)
```

**Step 2: Add TestGetCommentModel class**

Add to `tests/test_app_api.py`:

```python
class TestGetCommentModel:
    """Tests for get_comment_model() function."""

    def test_default_model(self):
        """Test that default model is tree_comments.Comment."""
        model = get_comment_model()
        assert model.__name__ == "Comment"
        assert model._meta.app_label == "tree_comments"

    def test_invalid_model_format(self, settings):
        """Test that invalid format raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_MODEL = "InvalidFormat"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_model()
        assert "must be of the form" in str(exc.value)

    def test_nonexistent_model(self, settings):
        """Test that nonexistent model raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_MODEL = "nonexistent.Model"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_model()
        assert "has not been installed" in str(exc.value)
```

**Step 3: Add TestGetCommentFlagModel class**

Add to `tests/test_app_api.py`:

```python
class TestGetCommentFlagModel:
    """Tests for get_comment_flag_model() function."""

    def test_default_model(self):
        """Test that default model is tree_comments.CommentFlag."""
        model = get_comment_flag_model()
        assert model.__name__ == "CommentFlag"
        assert model._meta.app_label == "tree_comments"

    def test_invalid_model_format(self, settings):
        """Test that invalid format raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_FLAG_MODEL = "InvalidFormat"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_flag_model()
        assert "must be of the form" in str(exc.value)
```

**Step 4: Add TestGetCommentForm class**

Add to `tests/test_app_api.py`:

```python
class TestGetCommentForm:
    """Tests for get_comment_form() function."""

    def test_default_form(self):
        """Test that default form is CommentForm."""
        form = get_comment_form()
        assert form.__name__ == "CommentForm"

    def test_custom_form_setting(self, settings):
        """Test custom form via TREE_COMMENTS_COMMENT_FORM."""
        settings.TREE_COMMENTS_COMMENT_FORM = "tree_comments.forms.CommentDetailsForm"
        form = get_comment_form()
        assert form.__name__ == "CommentDetailsForm"

    def test_invalid_form_import(self, settings):
        """Test that invalid form raises ImproperlyConfigured."""
        settings.TREE_COMMENTS_COMMENT_FORM = "nonexistent.Form"
        with pytest.raises(ImproperlyConfigured) as exc:
            get_comment_form()
        assert "could not be imported" in str(exc.value)
```

**Step 5: Add TestGetCommentFormTarget class**

Add to `tests/test_app_api.py`:

```python
class TestGetCommentFormTarget:
    """Tests for get_comment_form_target() function."""

    def test_returns_url(self):
        """Test that function returns correct URL."""
        url = get_comment_form_target()
        expected = reverse("tree-comments-post-comment")
        assert url == expected
```

**Step 6: Add TestGetFlagUrl class**

Add to `tests/test_app_api.py`:

```python
class TestGetFlagUrl:
    """Tests for get_flag_url() function."""

    def test_returns_correct_url(self, comment):
        """Test that function returns correct flag URL."""
        url = get_flag_url(comment)
        expected = reverse("tree-comments-flag", args=(comment.id,))
        assert url == expected

    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_flag_url(comment)
        assert str(comment.id) in url
```

**Step 7: Add TestGetDeleteUrl class**

Add to `tests/test_app_api.py`:

```python
class TestGetDeleteUrl:
    """Tests for get_delete_url() function."""

    def test_returns_correct_url(self, comment):
        """Test that function returns correct delete URL."""
        url = get_delete_url(comment)
        expected = reverse("tree-comments-delete", args=(comment.id,))
        assert url == expected

    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_delete_url(comment)
        assert str(comment.id) in url
```

**Step 8: Add TestGetApproveUrl class**

Add to `tests/test_app_api.py`:

```python
class TestGetApproveUrl:
    """Tests for get_approve_url() function."""

    def test_returns_correct_url(self, comment):
        """Test that function returns correct approve URL."""
        url = get_approve_url(comment)
        expected = reverse("tree-comments-approve", args=(comment.id,))
        assert url == expected

    def test_url_includes_comment_id(self, comment):
        """Test that URL includes the comment ID."""
        url = get_approve_url(comment)
        assert str(comment.id) in url
```

**Step 9: Run tests to verify they pass**

Run: `pytest tests/test_app_api.py -v`
Expected: All tests PASS

**Step 10: Commit**

```bash
git add tests/test_app_api.py
git commit -m "test: add comprehensive tests for public API functions

- Test get_comment_model() with default and custom settings
- Test get_comment_flag_model() with default and custom settings
- Test get_comment_form() with default and custom forms
- Test get_comment_form_target() returns correct URL
- Test get_flag_url(), get_delete_url(), get_approve_url()
- Test error handling for invalid configurations"
```

---

### Task 5: Create tox.ini Configuration

**Files:**
- Create: `tox.ini`

**Step 1: Create tox.ini with uv plugin**

Create `tox.ini`:

```ini
[tox]
envlist =
    py38-django{42,50,51}
    py39-django{42,50,51}
    py310-django{42,50,51,main}
    py311-django{42,50,51,main}
    py312-django{42,50,51,main}
minversion = 4.0

[testenv]
runner = uv-venv-lock-runner
deps =
    django42: Django>=4.2,<5.0
    django50: Django>=5.0,<5.1
    django51: Django>=5.1,<5.2
    django-main: https://github.com/django/django/archive/main.tar.gz
setenv =
    PYTHONWARNINGS = default
    DJANGO_SETTINGS_MODULE = tests.settings
commands =
    pytest {posargs}

[testenv:coverage]
runner = uv-venv-lock-runner
commands =
    pytest --cov=tree_comments --cov-report=term-missing --cov-report=xml

[gh]
python_versions =
    3.8=py38
    3.9=py39
    3.10=py310
    3.11=py311
    3.12=py312
```

**Step 2: Commit**

```bash
git add tox.ini
git commit -m "feat: add tox configuration with uv plugin

- Configure multi-version testing (Python 3.8-3.12, Django 4.2-5.1)
- Use uv-venv-lock-runner for fast dependency management
- Add coverage environment for test coverage reports
- Configure GitHub Actions integration"
```

---

### Task 6: Create GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Step 1: Create .github/workflows directory**

Run: `mkdir -p .github/workflows`

**Step 2: Create test.yml workflow**

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
        django-version: ['4.2', '5.0', '5.1']
        exclude:
          - python-version: '3.8'
            django-version: '5.0'
          - python-version: '3.8'
            django-version: '5.1'
        include:
          - python-version: '3.10'
            django-version: 'main'
          - python-version: '3.11'
            django-version: 'main'
          - python-version: '3.12'
            django-version: 'main'

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: 'latest'

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          uv pip install --system tox tox-uv

      - name: Run tests with tox
        run: tox -e py${{ matrix.python-version | replace('.', '') }}-django${{ matrix.django-version }}

      - name: Upload coverage to codecov
        if: matrix.python-version == '3.12' && matrix.django-version == '5.1'
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

**Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "feat: add GitHub Actions workflow for CI

- Test matrix: Python 3.8-3.12, Django 4.2-5.1, main
- Use uv for fast dependency installation
- Exclude Python 3.8 with Django 5.0+ (incompatible)
- Upload coverage reports to codecov
- Run on push to main and pull requests"
```

---

## Phase 3: Internationalization

### Task 7: Copy Locale Files from django-contrib-comments

**Files:**
- Create: `tree_comments/locale/` directory structure

**Step 1: Copy entire locale directory**

Run:
```bash
cp -r /home/alice/Workspace/django-contrib-comments/django_comments/locale tree_comments/
```

**Step 2: Verify locale files were copied**

Run: `ls tree_comments/locale/ | wc -l`
Expected: 70+ (number of language directories)

**Step 3: Commit**

```bash
git add tree_comments/locale/
git commit -m "feat: copy 70+ language translations from django-contrib-comments

Copy all locale files from django-contrib-comments as baseline for
tree_comments internationalization. Will be adapted in next commit."
```

---

### Task 8: Adapt Translation Strings

**Files:**
- Modify: All `tree_comments/locale/*/LC_MESSAGES/django.po` files

**Step 1: Create adaptation script**

Create temporary script `adapt_translations.py`:

```python
#!/usr/bin/env python3
"""
Adapt translation files from django-contrib-comments to tree_comments.
"""
import os
import re
from pathlib import Path

LOCALE_DIR = Path("tree_comments/locale")

# Replacements to make in all .po files
REPLACEMENTS = [
    ("django_comments", "tree_comments"),
    ("comments-flag", "tree-comments-flag"),
    ("comments-delete", "tree-comments-delete"),
    ("comments-approve", "tree-comments-approve"),
    ("comments-post-comment", "tree-comments-post-comment"),
    ("comments-comment-done", "tree-comments-comment-done"),
    ("comments-flag-done", "tree-comments-flag-done"),
    ("comments-delete-done", "tree-comments-delete-done"),
    ("comments-approve-done", "tree-comments-approve-done"),
    ("comments-url-redirect", "tree-comments-url-redirect"),
]

def adapt_po_file(po_file):
    """Apply replacements to a .po file."""
    content = po_file.read_text(encoding='utf-8')

    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    po_file.write_text(content, encoding='utf-8')
    print(f"Adapted: {po_file}")

def main():
    """Process all .po files in locale directory."""
    for lang_dir in LOCALE_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        po_file = lang_dir / "LC_MESSAGES" / "django.po"
        if po_file.exists():
            adapt_po_file(po_file)

if __name__ == "__main__":
    main()
```

**Step 2: Run adaptation script**

Run: `python adapt_translations.py`

**Step 3: Remove adaptation script**

Run: `rm adapt_translations.py`

**Step 4: Commit**

```bash
git add tree_comments/locale/
git commit -m "feat: adapt translations for tree_comments

- Replace django_comments with tree_comments
- Update all URL names to tree-comments-* pattern
- Apply changes to all 70+ language files"
```

---

### Task 9: Add Tree-Specific Translation Strings

**Files:**
- Modify: `tree_comments/models.py`
- Modify: `tree_comments/views.py`
- Modify: `tree_comments/forms.py`

**Step 1: Add translation imports to models.py**

Read: `tree_comments/models.py`

Add at top of file after other imports:

```python
from django.utils.translation import gettext_lazy as _
```

**Step 2: Add verbose_name translations to AbstractComment fields**

In `tree_comments/models.py`, update the `parent` field in `AbstractComment`:

```python
parent = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='children',
    verbose_name=_('parent comment'),
    help_text=_('The parent comment being replied to'),
)
```

**Step 3: Add translation imports to views.py**

Read: `tree_comments/views.py`

Add at top of file after other imports:

```python
from django.utils.translation import gettext_lazy as _
```

**Step 4: Add translation strings in ReplyView**

In `tree_comments/views.py`, find `ReplyView` class and add to get_context_data:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = _('Reply to comment')
    return context
```

**Step 5: Add translation imports to forms.py**

Read: `tree_comments/forms.py`

Add at top of file after other imports:

```python
from django.utils.translation import gettext_lazy as _
```

**Step 6: Add label translations to CommentDetailsForm**

In `tree_comments/forms.py`, update `CommentDetailsForm` Meta class:

```python
class Meta:
    model = Comment
    fields = ('comment', 'parent')
    labels = {
        'comment': _('Comment'),
        'parent': _('Parent comment'),
    }
```

**Step 7: Generate translation messages**

Run:
```bash
cd tree_comments
django-admin makemessages --all
```

**Step 8: Add English translations to django.pot**

The template file was created. Now add translations for English in `tree_comments/locale/en/LC_MESSAGES/django.po`:

```po
msgid "parent"
msgstr "parent"

msgid "parent comment"
msgstr "parent comment"

msgid "reply to comment"
msgstr "reply to comment"

msgid "threaded comments"
msgstr "threaded comments"

msgid "root comment"
msgstr "root comment"

msgid "children"
msgstr "children"

msgid "child comments"
msgstr "child comments"

msgid "thread depth"
msgstr "thread depth"

msgid "reply URL"
msgstr "reply URL"

msgid "tree structure"
msgstr "tree structure"

msgid "Reply to comment"
msgstr "Reply to comment"

msgid "The parent comment being replied to"
msgstr "The parent comment being replied to"
```

**Step 9: Add Chinese translations**

Add to `tree_comments/locale/zh_Hans/LC_MESSAGES/django.po`:

```po
msgid "parent"
msgstr "父级"

msgid "parent comment"
msgstr "父评论"

msgid "reply to comment"
msgstr "回复评论"

msgid "threaded comments"
msgstr "树状评论"

msgid "root comment"
msgstr "根评论"

msgid "children"
msgstr "子评论"

msgid "child comments"
msgstr "子评论"

msgid "thread depth"
msgstr "评论深度"

msgid "reply URL"
msgstr "回复链接"

msgid "tree structure"
msgstr "树状结构"

msgid "Reply to comment"
msgstr "回复评论"

msgid "The parent comment being replied to"
msgstr "被回复的父评论"
```

Add to `tree_comments/locale/zh_Hant/LC_MESSAGES/django.po`:

```po
msgid "parent"
msgstr "父級"

msgid "parent comment"
msgstr "父評論"

msgid "reply to comment"
msgstr "回覆評論"

msgid "threaded comments"
msgstr "樹狀評論"

msgid "root comment"
msgstr "根評論"

msgid "children"
msgstr "子評論"

msgid "child comments"
msgstr "子評論"

msgid "thread depth"
msgstr "評論深度"

msgid "reply URL"
msgstr "回覆連結"

msgid "tree structure"
msgstr "樹狀結構"

msgid "Reply to comment"
msgstr "回覆評論"

msgid "The parent comment being replied to"
msgstr "被回覆的父評論"
```

**Step 10: Compile translation messages**

Run:
```bash
cd tree_comments
django-admin compilemessages
```

**Step 11: Commit**

```bash
git add tree_comments/models.py tree_comments/views.py tree_comments/forms.py tree_comments/locale/
git commit -m "feat: add tree-specific translation strings

- Add verbose_name and help_text translations for parent field
- Add translation strings for reply functionality
- Add English and Chinese translations for tree-specific terms
- Generate and compile .po and .mo files"
```

---

## Phase 4: Documentation

### Task 10: Setup MkDocs Infrastructure

**Files:**
- Create: `mkdocs.yml`
- Create: `.readthedocs.yml`

**Step 1: Create mkdocs.yml**

Create `mkdocs.yml`:

```yaml
site_name: Django Tree Comments
site_description: A Django app for threaded comments using Common Table Expressions (CTE)
site_author: jukanntenn

theme:
  name: material
  palette:
    primary: blue
    accent: blue
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - toc.follow
    - search.suggest
    - search.highlight

repo_url: https://github.com/jukanntenn/django-tree-comments
repo_name: jukanntenn/django-tree-comments
edit_uri: edit/main/docs/

nav:
  - Home: index.md
  - Quick Start: quickstart.md
  - Settings: settings.md
  - Models: models.md
  - Forms: forms.md
  - Moderation: moderation.md
  - Signals: signals.md
  - Custom Apps: custom.md
  - Examples: examples.md
  - API Reference:
    - Managers: api/managers.md
    - Views: api/views.md
  - Migration Guide: migration.md
  - Architecture: architecture.md

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - toc:
      permalink: true
  - attr_list
  - md_in_html

plugins:
  - search

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/jukanntenn/django-tree-comments
```

**Step 2: Create .readthedocs.yml**

Create `.readthedocs.yml`:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
  jobs:
    post_create_environment:
      - pip install mkdocs mkdocs-material pymdown-extensions

mkdocs:
  configuration: mkdocs.yml
```

**Step 3: Create docs directory**

Run: `mkdir -p docs/api`

**Step 4: Commit**

```bash
git add mkdocs.yml .readthedocs.yml docs/
git commit -m "feat: setup MkDocs documentation infrastructure

- Configure MkDocs with Material theme
- Add navigation structure
- Configure ReadTheDocs deployment
- Add markdown extensions for syntax highlighting"
```

---

### Task 11: Convert Core Documentation Files

**Files:**
- Create: `docs/index.md`
- Create: `docs/quickstart.md`
- Create: `docs/settings.md`
- Create: `docs/models.md`
- Create: `docs/forms.md`

**Note:** These tasks involve converting RST to Markdown and adapting content. Due to length, I'll provide the structure and key adaptations for each file.

**Step 1: Create docs/index.md**

Create `docs/index.md`:

```markdown
# Django Tree Comments

A Django app for threaded comments using Common Table Expressions (CTE).

## Features

- **Threaded Comments**: Hierarchical comment structure with parent-child relationships
- **CTE Queries**: Efficient tree queries using PostgreSQL Common Table Expressions
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

- Python 3.8+
- Django 4.2+
- PostgreSQL (recommended) or SQLite 3.8.3+

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
- Built-in JSON API support for AJAX/AJAX requests
- Modern Python packaging with pyproject.toml

See the [full comparison](comparison/2026-03-01-django-contrib-comments-comparison.md) for details.

## License

BSD-3-Clause
```

**Step 2: Commit**

```bash
git add docs/index.md
git commit -m "docs: add index page with project overview"
```

**Step 3: Create docs/quickstart.md**

Create `docs/quickstart.md` with tree-specific examples:

```markdown
# Quick Start Guide

Get started with Django Tree Comments in 5 minutes.

## Installation

Install the package:

```bash
pip install django-tree-comments
```

Add to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'tree_comments',
    'django.contrib.contenttypes',
    'django.contrib.sites',
]
```

Run migrations:

```bash
python manage.py migrate
```

## Basic Usage

### Display Comments

Load the template tags in your template:

```django
{% load tree_comments %}

<h2>Comments</h2>
{% render_comment_list for object %}
```

### Display Comment Form

Add a comment form:

```django
{% render_comment_form for object %}
```

### Threaded Comments

Display threaded comments with parent-child relationships:

```django
{% get_comment_list for object as comment_list %}
{% for comment in comment_list %}
    <div class="comment" style="margin-left: {{ comment.level }}em;">
        {{ comment.comment }}
        <a href="{{ comment.get_reply_url }}">Reply</a>
    </div>
{% endfor %}
```

### JSON API

Get comments as JSON for AJAX:

```python
import requests

response = requests.get(
    '/comments/form/',
    headers={'Accept': 'application/json'},
    params={'content_type': 'blog.article', 'object_id': 1}
)
data = response.json()
```

## Next Steps

- Read the [Settings](settings.md) documentation
- Learn about [Models](models.md) and query methods
- See [Examples](examples.md) for more use cases
```

**Step 4: Commit**

```bash
git add docs/quickstart.md
git commit -m "docs: add quickstart guide with tree-specific examples"
```

**Step 5: Create docs/settings.md**

Create `docs/settings.md`:

```markdown
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
```

**Step 6: Commit**

```bash
git add docs/settings.md
git commit -m "docs: add settings documentation for tree_comments"
```

**Continue with remaining documentation files following the same pattern...**

---

### Task 12-20: Continue Documentation Conversion

Due to length constraints, continue with these documentation files following the same pattern:

- Task 12: Create `docs/models.md` - Document Comment model with parent field and tree methods
- Task 13: Create `docs/forms.md` - Document forms with parent parameter
- Task 14: Create `docs/moderation.md` - Document moderation system
- Task 15: Create `docs/signals.md` - Document all signals
- Task 16: Create `docs/custom.md` - Document swappable models approach
- Task 17: Create `docs/examples.md` - Tree-specific examples
- Task 18: Create `docs/migration.md` - Migrating from django-contrib-comments
- Task 19: Create `docs/architecture.md` - CTE queries, CBV design, JSON API
- Task 20: Create `docs/api/managers.md` and `docs/api/views.md` - API reference

Each task should:
1. Create the file
2. Convert RST to Markdown
3. Adapt content for tree_comments
4. Add tree-specific examples
5. Commit with descriptive message

---

## Final Steps

### Task 21: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest -v`

Expected: All tests PASS

**Step 2: Run tests with coverage**

Run: `pytest --cov=tree_comments --cov-report=term-missing`

Expected: Coverage >90% for new code

### Task 22: Verify Documentation Build

**Step 1: Install docs dependencies**

Run: `pip install -e ".[docs]"`

**Step 2: Build documentation**

Run: `mkdocs build`

Expected: Documentation builds successfully

**Step 3: Preview documentation**

Run: `mkdocs serve`

Open: http://127.0.0.1:8000

Expected: Documentation renders correctly

### Task 23: Final Commit and Push

**Step 1: Review all changes**

Run: `git status`

**Step 2: Push to remote**

Run: `git push origin 0.0.4`

---

## Success Criteria

- [ ] All three API functions added and tested
- [ ] All 70+ languages migrated with tree-specific strings
- [ ] Complete documentation in MkDocs with Material theme
- [ ] CI/CD running tests across Python 3.8-3.12 and Django 4.2-5.1
- [ ] pyproject.toml updated with comprehensive metadata
- [ ] Test coverage >90% for new code
- [ ] All tests passing
- [ ] Documentation builds successfully

## Notes for Implementation

- Each task should be completed in order
- Run tests after each code change
- Commit frequently with descriptive messages
- If a test fails, fix it before moving to next task
- Use `superpowers:verification-before-completion` before claiming completion
