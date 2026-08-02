---
name: release
description: >
  Use when the user wants to publish a new version, create a release, bump the
  version, or says things like "release 0.0.4", "publish a new version", "cut a
  release", "ship it", or "prepare release".
---

# Release

Version lives in one place: `tree_comments/__init__.py` `__version__` (hatchling reads it dynamically; `pyproject.toml` has `dynamic = ["version"]` — never write a literal `version` there). A release touches that file, `CHANGELOG.md`, and `uv.lock`.

Validate before proceeding; on failure report + STOP, never auto-fix. At each 🛑 PAUSE wait for an explicit affirmative (ok / 确认 / yes / LGTM / proceed / confirm); silence or vague replies are not consent.

## Prerequisites

```bash
git status                                          # clean
grep __version__ tree_comments/__init__.py          # current version
git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAGS"   # last tag (initial commit if none)
git log --oneline <last_tag_or_initial>..HEAD       # commits since last release
```

## 1. Checks

```bash
uv run prek run --all-files     # ruff / djlint / mypy / pyproject-fmt / django-upgrade
uv run pytest
```

Fail → report + STOP.

## 2. Version

PEP 440 (`X.Y.Z` or `X.Y.Zrc1`/`a1`/`b1`); `0.0.4rc1` not `0.0.4-rc1`. Higher than current; tag `vX.Y.Zrc1` must not exist. If the user gave no version, recommend (patch=fix / minor=feature / rcN=release candidate) with reasoning.

Update `tree_comments/__init__.py` → `__version__ = "X.Y.Zrc1"`, then `uv build` and confirm dist filenames show the new version.

**🛑 PAUSE — confirm version.**

## 3. CHANGELOG

Insert a `## [X.Y.Zrc1] - YYYY-MM-DD` section under `## [Unreleased]` (Keep a Changelog format; omit empty sections). Update the bottom compare links. User-facing wording (what changed for users, not code internals).

**🛑 PAUSE — review CHANGELOG entry.**

## 4. Pre-tag summary

Confirm: version in `__init__.py` == CHANGELOG heading; `uv build` succeeded; AGENTS.md/CLAUDE.md still byte-identical if touched.

**🛑 PAUSE — confirm ready to commit and tag.**

## 5. Commit + tag

```bash
git add tree_comments/__init__.py CHANGELOG.md uv.lock
git commit -m "chore: release vX.Y.Zrc1"
git tag -a vX.Y.Zrc1 -m "Release vX.Y.Zrc1"
git tag -l "vX.Y.Zrc1"          # verify exactly one
```

prek failure → report + STOP. Never `--no-verify`.

## 6. Push

Pushing the tag triggers `release.yml` → test → build → TestPyPI → PyPI (Trusted Publishing) → GitHub Release (CHANGELOG body via `mindsers/changelog-reader-action`, rc marked prerelease). Effectively irreversible.

**🛑 PAUSE — confirm push.**

```bash
git push && git push origin vX.Y.Zrc1
```

## 7. Verify

Actions green, version on PyPI, GitHub Release body matches CHANGELOG:
- `https://github.com/jukanntenn/django-tree-comments/actions/workflows/release.yml`
- `https://pypi.org/project/django-tree-comments/X.Y.Zrc1/`
- `https://github.com/jukanntenn/django-tree-comments/releases/tag/vX.Y.Zrc1`

Requires one-time Trusted Publishing setup: PyPI env `pypi` + TestPyPI env `testpypi`, both for workflow `release.yml` / jobs `publish-pypi` / `publish-testpypi`; matching GitHub environments.
