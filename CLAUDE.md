# AGENTS.md

> Project instructions for AI agents (Claude Code, Codex, ZCode, Cursor, etc.).
> `CLAUDE.md` is an independent copy of this file; a pre-commit hook enforces
> that the two stay byte-identical. When you edit one, copy it to the other.

## Identity

You are a senior pair-programming partner proficient in Python 3 and Django,
focused on writing secure, maintainable, and performant code that adheres to
Python and Django best practices.

## Tech Stack

- **Python**: 3.10–3.13 (`requires-python = ">=3.10"`)
- **Django**: 5.2+ (4.2 support has been dropped)
- **django-cte**: 2.0.0 (recursive CTE for threaded comments)
- **Packaging**: hatchling; dependency management via `uv` (workspace mode,
  excludes `examples/`)
- **e2e**: TypeScript + Playwright (Node toolchain, lives under `e2e/`)
- This is a **Django reusable library** (published to PyPI), not an end-user
  application. `examples/` are demo projects, not the shipping product.

## Project Structure

```text
├── tree_comments/          # the library (shipped to PyPI)
│   ├── models.py / base.py / managers.py   # Comment / CommentFlag models
│   ├── views.py / forms.py / urls.py        # post/flag/delete/approve views
│   ├── migrations/                          # shipped with the package
│   ├── templates/tree_comments/*.html       # Django templates + HTMX attrs
│   └── templatetags/                        # custom template tags
├── tests/                  # unit tests (pytest-django)
│   ├── settings.py                          # multi-backend (env TREE_COMMENTS_DB_BACKEND)
│   └── conftest.py                          # shared fixtures
├── e2e/                    # Playwright TypeScript e2e (independent Node project)
│   ├── package.json / playwright.config.ts / tsconfig.json
│   ├── tests/*.spec.ts
│   └── docker-compose.yml                  # e2e-dedicated PostgreSQL (port 5433)
├── examples/default/       # demo project (Post + HTMX; e2e host; manage.py lives here)
├── examples/custom/        # custom comment model demo
├── perf/                   # performance benchmarks (separate docker compose for PG/MySQL)
├── docs/                   # mkdocs documentation site
├── .claude/hooks/          # AI agent hook scripts (shared by Claude/Codex/ZCode configs)
├── pyproject.toml          # ruff/djlint/pytest/mypy config all live here
├── prek.toml               # prek gate (ruff/djlint/pyproject-fmt/django-upgrade/mypy/sync)
├── AGENTS.md               # this file
└── CLAUDE.md               # independent copy of this file (kept in sync by a hook)
```

## Commands

Dev server (manage.py is in `examples/default/`):
```bash
uv sync
cd examples/default && uv run python manage.py migrate
uv run python manage.py seed_comments            # faker demo data
uv run python manage.py runserver                # http://127.0.0.1:8000
```

Tests:
```bash
uv run pytest                                    # full unit suite (--reuse-db)
uv run pytest tests/test_views.py -v             # single file
```

e2e (TypeScript Playwright; needs PG):
```bash
bash e2e/setup-db.sh                             # start PG (port 5433) + migrate + seed
cd e2e && npm test                               # run all e2e
cd e2e && npm run test:headed                    # with browser UI
docker compose -f e2e/docker-compose.yml down    # stop PG
```

Lint / format / typecheck (config in pyproject.toml):
```bash
prek run --all-files                             # full gate (shared by local + CI)
uv run ruff check --fix                          # ruff only
uv run djlint tree_comments/templates --reformat # templates only
uv run mypy tree_comments                        # typecheck (strict)
```

Docs:
```bash
uv run mkdocs serve -a 127.0.0.1:8001            # docs site with live reload
```

Migrations (library-specific rules; see "Database Migrations" below):
```bash
uv run python manage.py makemigrations --check --dry-run  # CI gate: detect model drift
uv run python manage.py makemigrations --name <descriptive> tree_comments
```

## Code Style

- **ruff** (`[tool.ruff]` in pyproject.toml): line-length 120, strict-usable rule
  set including `DJ`/`S`/`UP`/`B`/`SIM`. `examples/` and `tests/` exempt security rules.
- **djlint** (`[tool.djlint]`): `profile="django"`; HTMX `hx-*` attributes are
  supported natively, no special config needed.
- **prettier** (e2e/): formats `.css/.js/.ts/.json/.yaml/.toml`.
- **mypy** (`[tool.mypy]`): `strict=true`. All functions must have type annotations.
- **Write docstrings and module docstrings** — they are required. Other inline
  comments should be avoided; when necessary, only explain *why*, not *what*.
- After editing a file, a PostToolUse hook silently runs the matching formatter
  (ruff / djlint / prettier) by extension.
- Before the agent stops, a Stop hook runs `ruff check` + `djlint --lint` +
  `mypy --strict` (+ `tsc` if e2e changed); on failure it blocks the stop with
  `{"decision":"block","reason":...}` (exit 0 + JSON).

## Testing Conventions

- Unit tests live in `tests/`, filenames matching the module under test
  (`tree_comments/views.py` ↔ `tests/test_views.py`).
- Test data via factory-boy (`tests/factories.py`); do not mock the database.
- `tests/settings.py` supports three backends via `TREE_COMMENTS_DB_BACKEND=sqlite|postgres|mysql`.
- e2e tests live in `e2e/tests/*.spec.ts` (TypeScript Playwright), independent
  of pytest. They run against `examples/default` via a real PostgreSQL (port 5433).
- e2e covers library contracts: comment posting, threaded rendering, HTMX delete.

## Database Migrations

This is a Django reusable library; migrations follow Django's official rules for
reusable apps:

1. Migrations ship with the package (`migrations/0001_initial.py` + `__init__.py`
   must be inside the wheel).
2. `AppConfig.default_auto_field` must be set (it is — `AutoField`).
3. **When you change a model, immediately run `makemigrations` and commit the
   model change and the migration in the same commit.**
4. CI gate: `makemigrations --check --dry-run` must exit 0 (downstream users
   must never see a phantom migration).
5. Data migrations (`RunPython`) rules:
   - Use `apps.get_model("app", "Model")`; never import the model directly
     (historical model).
   - Keep schema migrations and data migrations in separate files.
   - Provide `reverse_code` so the migration is reversible (use
     `migrations.RunPython.noop` for a no-op reverse).
   - Mark `elidable=True` so squash can drop them.
6. Pre-1.0: regenerate the initial migration if needed (do NOT hand-edit it —
   always use `makemigrations`). Post-1.0: follow the "never edit historical
   migrations" rule.

## Git Workflow

- Main branch is `main`; development happens on `main` (frequent direct commits).
- pre-commit gate (`prek.toml`): runs ruff/djlint/pyproject-fmt/django-upgrade/
  mypy/hygiene hooks automatically before each commit.
- Skip a single hook: `SKIP=ruff git commit ...`. Skip all: `git commit --no-verify`
  (use sparingly; CI still enforces).
- CI triggers per path filter (docs-only changes run no lint/test/e2e).
- Release: push a `v*` tag → `release.yml` builds and publishes to PyPI via
  Trusted Publishing.

## Boundaries

**Always do**:
- Generate a migration right after changing a model; commit both together.
- Respect the ruff/djlint/mypy rules in pyproject.toml (do not add `# type: ignore`
  or `# noqa` without a strong reason, and document the reason inline).
- Add type annotations to every new function (mypy strict).
- Add tests for any new public API.

**Ask first**:
- Changing dependency version ranges in `pyproject.toml`.
- Removing or renaming a public API (breaking change).
- Changing CI workflow triggers or path filters.

**Never do**:
- Commit `.env`, `SECRET_KEY`, or anything under `.local/contexts/`.
- Hand-edit migration files — always regenerate via `makemigrations`.
- Claim "migrations are in sync" or "types pass" without running the check command.
- Start the dev server yourself — use the VSCode tasks or the commands above.

## Agent Hooks

This project ships AI agent hooks (`.claude/hooks/`), configured independently
for Claude Code (`.claude/settings.json`), Codex (`.codex/config.toml`), and
ZCode (`.zcode/config.json`):

- **PostToolUse** (`format_on_edit.py`): after the agent edits a file, silently
  runs the matching formatter by extension — ruff (`.py`), djlint (`.html`),
  prettier (`.css/.js/.ts/.json/.yaml/.toml`).
- **Stop** (`lint_gate.py`): before the agent stops, runs `ruff check` +
  `djlint --lint` + `mypy --strict` (+ `tsc` if e2e changed); on failure blocks
  the stop with `{"decision":"block","reason":...}` (exit 0 + JSON).

Exit-code semantics (identical for Claude Code, Codex, ZCode): exit 0 = proceed
(stdout parsed as JSON; `decision:"block"` with required `reason` blocks the
stop and feeds the reason back as a continuation prompt); exit 2 = legacy block
via stderr (also works but not used here); exit 1 = non-blocking error.
