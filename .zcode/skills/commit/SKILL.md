---
name: commit
description: Use when the user asks to commit or stage changes (commit/stage/save/submit), when a task ends with dirty files to commit, or when multiple files should be split into logical commits.
---

# Commit

Group by logical change, not by file. Draft a plan, confirm, then execute. Never push, never amend.

1. `git status --porcelain` + `git log --oneline -5` for current changes and history style.
2. Separate AI-edited files from unrecognized ones; list unrecognized separately, never mix them in.
3. Group by logical unit, order: `chore` → `feat` → `fix` → `refactor` → `docs` → `test` → `ci`, `release` last.
4. Present the plan once; after confirmation run `git add` + `git commit` batch by batch. Rejected → stop.
5. prek runs automatically (ruff / djlint / mypy / pyproject-fmt / django-upgrade); never `--no-verify`.
6. Single file → skip the plan, commit directly.

Message: `<type>: <desc>` — lowercase, imperative, no trailing period. Types: `feat`/`fix`/`docs`/`refactor`/`test`/`ci`/`chore`. No scopes.

- Generated files (lockfile, migrations) bundle into the producing commit, or as a standalone `chore`.
- AGENTS.md and CLAUDE.md must be byte-identical (the `agents-claude-sync` hook rejects divergence).
- Never silently include unrecognized files. Never amend, never push, never placeholder messages (wip, update files).
