# Django-Tree-Comments Migration Design

**Date:** 2026-03-03
**Status:** Draft
**Scope:** Migration from django-contrib-comments to django-tree-comments

## Overview

This design outlines the migration of missing features from django-contrib-comments to django-tree-comments based on the comprehensive comparison document. The migration focuses on six key areas:

1. Missing public API functions
2. Internationalization (70+ languages)
3. Documentation (MkDocs + Material theme)
4. CI/CD configuration (tox + GitHub Actions)
5. pyproject.toml improvements
6. Test coverage improvements

## Section 1: Public API Functions

### Objective

Add three missing URL helper functions to match django-contrib-comments API.

### Implementation

**Location:** `tree_comments/__init__.py`

Add three functions following the same pattern as `get_comment_form_target()`:

```python
def get_flag_url(comment):
    """
    Get the URL for the "flag this comment" view.
    """
    return reverse("tree-comments-flag", args=(comment.id,))


def get_delete_url(comment):
    """
    Get the URL for the "delete this comment" view.
    """
    return reverse("tree-comments-delete", args=(comment.id,))


def get_approve_url(comment):
    """
    Get the URL for the "approve this comment from moderation" view.
    """
    return reverse("tree-comments-approve", args=(comment.id,))
```

### Design Decisions

- **Simple reverse lookup:** No custom app delegation (unlike django-contrib-comments)
- **Consistent naming:** Follow existing `get_comment_*` naming pattern
- **URL names:** Use existing URL names from `tree_comments/urls.py`

## Section 2: Internationalization (i18n)

### Objective

Migrate all 70+ language translations and add new strings for tree-specific features.

### Implementation

#### 2.1 Copy Locale Structure

Copy all language directories from django-contrib-comments:
- Source: `/home/alice/Workspace/django-contrib-comments/django_comments/locale/`
- Target: `tree_comments/locale/`
- Structure: `<lang>/LC_MESSAGES/django.po`

#### 2.2 Adapt Existing Translations

For each `.po` file:
1. Replace "django_comments" → "tree_comments"
2. Update URL names in translation strings:
   - "comments-flag" → "tree-comments-flag"
   - "comments-delete" → "tree-comments-delete"
   - "comments-approve" → "tree-comments-approve"
   - "comments-post-comment" → "tree-comments-post-comment"
3. Adapt domain-specific terminology where context requires

#### 2.3 Add Tree-Specific Translation Strings

**New strings to add:**

```python
# In models.py, views.py, forms.py, etc.
gettext("parent")
gettext("parent comment")
gettext("reply")
gettext("reply to comment")
gettext("threaded comments")
gettext("root comment")
gettext("children")
gettext("child comments")
gettext("thread depth")
gettext("reply URL")
gettext("tree structure")
```

**Process:**
1. Add `gettext()` calls in Python code
2. Run `django-admin makemessages --all` to generate `.po` entries
3. Provide English translations as defaults
4. Translate to Chinese (zh_Hans, zh_Hant) as initial non-English support
5. Run `django-admin compilemessages` to create `.mo` files

### Languages to Migrate

All 70+ languages from django-contrib-comments:
```
af, ar, az, be, bg, bn, br, bs, ca, cs, cy, da, de, el, en, en_GB, eo, es,
es_AR, es_MX, et, eu, fa, fi, fr, fy, fy_NL, ga, gd, gl, he, hi, hr,
hu, ia, id, is, it, ja, ka, kk, km, kn, ko, kq, lv, mk, ml, mn, mr,
ms, my, nb, ne, nl, nn, no, os, pa, pl, pt, pt_BR, ro, ru, sk, sl,
sq, sr, sr_Latn, sv, sw, ta, te, th, tk, tr, tt, ug, uk, ur, vi,
zh_Hans, zh_Hant
```

## Section 3: Documentation

### Objective

Create comprehensive documentation using MkDocs with Material theme, converted from Sphinx RST to Markdown.

### Implementation

#### 3.1 Setup MkDocs Infrastructure

**Create `mkdocs.yml`:**

```yaml
site_name: Django Tree Comments
theme:
  name: material
  palette:
    primary: blue
    accent: blue
  features:
    - navigation.tabs
    - navigation.sections
    - toc.follow

repo_url: https://github.com/jukanntenn/django-tree-comments
repo_name: jukanntenn/django-tree-comments

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
  - pymdownx.highlight
  - pymdownx.superfences
  - admonition
  - toc:
      permalink: true
```

**Add dependencies to pyproject.toml:**

```toml
[project.optional-dependencies]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "pymdown-extensions>=10.0.0",
]
```

**Create `.readthedocs.yml`:**

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

#### 3.2 Convert Documentation Files

| Source (RST) | Target (Markdown) | Adaptations |
|--------------|-------------------|-------------|
| `index.txt` | `docs/index.md` | Highlight threaded comments, CTE queries |
| `quickstart.txt` | `docs/quickstart.md` | Add tree structure examples |
| `settings.txt` | `docs/settings.md` | Document `TREE_COMMENTS_*` settings |
| `models.txt` | `docs/models.md` | Add parent field, tree methods |
| `forms.txt` | `docs/forms.md` | Document parent param, `as_json()` |
| `moderation.txt` | `docs/moderation.md` | Keep moderation docs |
| `signals.txt` | `docs/signals.md` | Document all signals |
| `custom.txt` | `docs/custom.md` | Swappable models approach |
| `example.txt` | `docs/examples.md` | Tree-specific examples |
| `management_commands.txt` | `docs/management-commands.md` | Keep as-is |
| `porting.txt` | `docs/migration.md` | Migrating from django-contrib-comments |

#### 3.3 Create New Documentation

**`docs/architecture.md`:**
- CTE-based tree queries explanation
- Class-based views design philosophy
- JSON API support
- Performance characteristics

**`docs/api/managers.md`:**
- `CommentManager.visible()` - Get visible comments
- `CommentManager.roots()` - Get root comments
- `CommentManager.cte_for_instance()` - CTE tree query
- Query optimization tips

**`docs/api/views.md`:**
- All CBV views documented
- Mixin classes explained
- JSON response handling
- Format parameter usage

**`docs/comparison.md`:**
- Link to existing comparison document
- Highlight key differences

#### 3.4 Content Adaptation Strategy

**For each document:**
1. Convert RST syntax to Markdown
2. Replace `django_comments` → `tree_comments`
3. Update URL names throughout
4. Add tree-specific examples and explanations
5. Highlight advantages: CTE queries, JSON responses, CBV architecture
6. Add code examples showing threaded comment usage
7. Include diagrams for tree structure concepts

## Section 4: CI/CD Configuration

### Objective

Create comprehensive CI/CD with tox (using uv plugin) and GitHub Actions.

### Implementation

#### 4.1 tox.ini Configuration

**Create `tox.ini`:**

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

#### 4.2 GitHub Actions Workflow

**Create `.github/workflows/test.yml`:**

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
        run: tox -e py${{ matrix.python-version }}-django${{ matrix.django-version }}

      - name: Upload coverage to codecov
        if: matrix.python-version == '3.12' && matrix.django-version == '5.1'
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

#### 4.3 Coverage Configuration

**Add to `pyproject.toml`:**

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

## Section 5: pyproject.toml Improvements

### Objective

Modernize package metadata with comprehensive information and best practices.

### Implementation

**Updated `pyproject.toml`:**

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

[project.urls]
Homepage = "https://github.com/jukanntenn/django-tree-comments"
Documentation = "https://django-tree-comments.readthedocs.io"
Repository = "https://github.com/jukanntenn/django-tree-comments"
Changelog = "https://github.com/jukanntenn/django-tree-comments/blob/main/CHANGELOG.md"
Issues = "https://github.com/jukanntenn/django-tree-comments/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.sdist]
include = ["tree_comments"]

[tool.hatch.build.targets.wheel]
include = ["tree_comments"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.settings"
python_files = "tests.py test_*.py"
addopts = "-v --tb=short"

[tool.uv.workspace]
exclude = ["examples/default", "examples/custom"]

[tool.ruff]
exclude = ["**/migrations/"]

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

### Key Changes

1. **Python version:** `>=3.8` (dropped 3.7)
2. **Django dependency:** Explicit `django>=4.2`
3. **Classifiers:** Comprehensive PyPI classifiers
4. **Optional dependencies:** Organized into `test`, `dev`, `docs` extras
5. **Project URLs:** Documentation, changelog, issues
6. **Keywords:** Expanded with relevant terms
7. **Coverage config:** Added coverage settings

## Section 6: Test Coverage Improvements

### Objective

Create comprehensive tests for swappable models and new API functions.

### Implementation

**Create `tests/test_app_api.py`:**

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


class TestGetCommentModel:
    """Tests for get_comment_model() function."""

    def test_default_model(self):
        """Test that default model is tree_comments.Comment."""
        model = get_comment_model()
        assert model.__name__ == "Comment"
        assert model._meta.app_label == "tree_comments"

    def test_custom_model_setting(self, settings):
        """Test custom model via TREE_COMMENTS_COMMENT_MODEL."""
        settings.TREE_COMMENTS_COMMENT_MODEL = "app.CustomComment"
        # This would require a custom model to be defined
        # For now, just test the setting is read
        # In real test, would create CustomComment model

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


class TestGetCommentFormTarget:
    """Tests for get_comment_form_target() function."""

    def test_returns_url(self):
        """Test that function returns correct URL."""
        url = get_comment_form_target()
        expected = reverse("tree-comments-post-comment")
        assert url == expected


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

### Test Fixtures

**Add to `tests/conftest.py`:**

```python
import pytest
from tree_comments.models import Comment


@pytest.fixture
def comment(db):
    """Create a test comment."""
    return Comment.objects.create(
        comment="Test comment",
        content_object=None,  # Would need a real object
    )
```

## Implementation Order

### Phase 1: Core API (Foundation)
1. Add missing public API functions to `tree_comments/__init__.py`
2. Update `pyproject.toml` with improvements

### Phase 2: Testing (Validation)
3. Create `tests/test_app_api.py` with comprehensive tests
4. Create `tox.ini` with uv plugin
5. Create `.github/workflows/test.yml`

### Phase 3: Internationalization (Content)
6. Copy all 70+ locale files from django-contrib-comments
7. Adapt translations (replace django_comments → tree_comments)
8. Add new translation strings for tree-specific features
9. Generate and compile translation files

### Phase 4: Documentation (Content)
10. Setup MkDocs infrastructure (mkdocs.yml, .readthedocs.yml)
11. Convert all documentation from RST to Markdown
12. Adapt and expand content for tree_comments features
13. Create new documentation sections (architecture, API reference)

## Success Criteria

- [ ] All three API functions added and working
- [ ] All 70+ languages migrated with tree-specific strings added
- [ ] Complete documentation in MkDocs with Material theme
- [ ] CI/CD running tests across Python 3.8-3.12 and Django 4.2-5.1
- [ ] pyproject.toml updated with comprehensive metadata
- [ ] Test coverage >90% for new code
- [ ] All tests passing in CI

## Risks and Mitigations

**Risk:** Translation quality for tree-specific features
- **Mitigation:** Start with English and Chinese translations, use native speakers for review

**Risk:** Documentation conversion introduces errors
- **Mitigation:** Manual review of each converted document, test all code examples

**Risk:** CI configuration complexity with uv plugin
- **Mitigation:** Test tox configuration locally before pushing, use uv's official documentation

**Risk:** Breaking changes in API
- **Mitigation:** All new functions are additions, no modifications to existing API

## Out of Scope

The following items from the comparison document are explicitly excluded:
- `get_comment_app()` and `get_comment_app_name()` (different architecture)
- Coverage reporting integration (optional enhancement)
- pre-commit hooks (optional enhancement)
- CONTRIBUTING.md and SECURITY.md (future work)
