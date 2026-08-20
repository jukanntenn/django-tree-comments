# AGENTS.md

> Project instructions for AI agents (Claude Code, Codex, ZCode, Cursor, etc.).
> `CLAUDE.md` and the `.agents/skills/` + `.zcode/skills/` mirrors are generated
> from this file and `.claude/skills/` by `scripts/sync_agents.py` (run
> automatically by the prek `agents-sync` hook). Never edit them directly.

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
│   ├── prek.toml                            # e2e hooks (prettier/tsc/lock check)
│   ├── tests/*.spec.ts
│   └── docker-compose.yml                  # e2e-dedicated PostgreSQL (port 5433)
├── examples/default/       # demo project (Post + HTMX; e2e host; manage.py lives here)
├── examples/custom/        # custom comment model demo
├── perf/                   # performance benchmarks (separate docker compose for PG/MySQL)
├── docs/                   # mkdocs documentation site
├── scripts/                # helper scripts (Python, cross-platform, stdlib-only)
├── .claude/.codex/.zcode/.opencode/  # AI agent hooks (thin wrappers over prek)
├── pyproject.toml          # ruff/djlint/pytest/mypy config all live here
├── prek.toml               # quality gate single source of truth (format/lint/check groups)
├── AGENTS.md               # this file (source of truth for agent instructions)
└── CLAUDE.md               # generated from AGENTS.md — never edit directly
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

Quality gate — prek is the single source of truth (`prek.toml` + `e2e/prek.toml`;
the AI hooks and CI are thin wrappers over the same config, so local green
means CI green). Hooks are tagged into three groups: `format` (mutating
fixers), `lint` (fast checks), `check` (slower verification gates: mypy/tsc/
locks/migrations/sync):
```bash
uv run prek install                             # first time: write git hook shims
uv run prek run --all-files                     # full gate (identical to CI)
uv run prek run --group format --files <file>   # what the AI post-edit hook runs
uv run prek run --group lint --group check --all-files  # what the AI stop hook runs
uv run prek run ruff-check                      # single hook by id
SKIP=ruff-check git commit ...                  # skip a single hook
```
Every tool comes from the uv dev environment (versions pinned by `uv.lock`).
e2e hooks need Node deps: `cd e2e && npm ci` (they skip with a hint otherwise;
CI installs and enforces them).

Docs:
```bash
uv run mkdocs serve -a 127.0.0.1:8001            # docs site with live reload
```

Migrations (library-specific rules; see "Database Migrations" below):
```bash
uv run python manage.py makemigrations --check --dry-run  # drift gate (also a prek check hook)
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
- After editing a file, a PostToolUse hook silently runs
  `uv run prek run --group format --files <edited>` — prek routes the file to
  the right fixer by extension and project (root vs e2e workspace).
- Before the agent stops, a Stop hook runs
  `uv run prek run --group lint --group check --all-files`; on failure it
  blocks the stop with `{"decision":"block","reason":...}` (exit 0 + JSON).

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
4. Drift gate: the prek `migrations-drift` check hook (and CI via the same
   prek gate) runs `makemigrations --check --dry-run` — it must exit 0
   (downstream users must never see a phantom migration).
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
- pre-commit gate (`prek.toml`, all three groups) runs automatically before each
  commit; a commit-msg hook enforces Conventional Commits.
- Skip a single hook: `SKIP=ruff-check git commit ...`. Skip all:
  `git commit --no-verify` (use sparingly; CI still enforces).
- CI lint job runs the exact same prek gate after `uv sync` + e2e `npm ci`;
  test/e2e/release are separate workflows (tox matrix, Playwright, PyPI).
- Release: push a `v*` tag → `release.yml` builds and publishes to PyPI via
  Trusted Publishing.

## Boundaries

**Always do**:
- Generate a migration right after changing a model; commit both together.
- Respect the ruff/djlint/mypy rules in pyproject.toml (do not add `# type: ignore`
  or `# noqa` without a strong reason, and document the reason inline).
- Add type annotations to every new function (mypy strict).
- Add tests for any new public API.
- Run `uv run prek run --all-files` before declaring work done.

**Ask first**:
- Changing dependency version ranges in `pyproject.toml`.
- Removing or renaming a public API (breaking change).
- Changing CI workflow triggers or path filters.

**Never do**:
- Commit `.env`, `SECRET_KEY`, or anything under `.local/contexts/`.
- Hand-edit generated files: migrations (regenerate via `makemigrations`),
  `CLAUDE.md` / `.agents/skills/` / `.zcode/skills/` (run
  `uv run python scripts/sync_agents.py`), or lock files (regenerate with
  `uv lock` / `npm install`).
- Claim "migrations are in sync" or "types pass" without running the check command.
- Start the dev server yourself — use the VSCode tasks or the commands above.

## Agent Hooks

The AI agent hooks under `.claude/`, `.codex/`, `.zcode/` and `.opencode/` are
**thin wrappers over prek** — the single source of truth for all formatting and
linting. No formatter/lint logic may live in a hook script; each adapter only
translates its tool's payload into a prek invocation.

- **PostToolUse** (after Edit/Write/apply_patch): runs
  `uv run prek run --group format --files <edited>` — prek routes the file to
  the right fixer by extension and project (root vs e2e workspace).
- **Stop**: runs `uv run prek run --group lint --group check --all-files`;
  on failure it blocks the stop with `{"decision":"block","reason":...}` (exit
  0 + JSON; once per turn, guarded by the stop-active flag).
- ZCode wires these via the user-level `~/.zcode/cli/config.json` because the
  runtime strips workspace hook configs — see `.zcode/README.md`.
- OpenCode cannot block on stop (its event hooks are fire-and-forget), so its
  plugin only formats post-edit; lint enforcement falls back to the prek
  pre-commit gate and CI.

Exit-code semantics (identical for Claude Code, Codex, ZCode): exit 0 = proceed
(stdout parsed as JSON; `decision:"block"` with required `reason` blocks the
stop and feeds the reason back as a continuation prompt); exit 2 = legacy block
via stderr (also works but not used here); exit 1 = non-blocking error.

Full design and verification notes: `docs/agent-hooks.md`.
