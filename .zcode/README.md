# ZCode Hooks

Project-local hook scripts for the ZCode agent. They are **thin adapters** that
delegate all formatting/linting to prek — the single source of truth (the
`format`, `lint` and `check` groups in `prek.toml` + `e2e/prek.toml`). No
formatter mapping lives in these scripts, so they cannot drift from prek/CI.

- `hooks/post_tool_use.py` — PostToolUse (`Edit|Write`): runs
  `uv run prek run --group format --files <edited>`. prek routes the file to
  the right project fixer (ruff / djlint / prettier / builtin byte fixers) at
  the correct cwd. Never blocks; real errors are surfaced to stderr.
- `hooks/stop.py` — Stop: runs
  `uv run prek run --group lint --group check --all-files` (ruff, djlint,
  mypy, tsc, lock/migrations/sync gates); on non-zero exit it prints
  `{"decision":"block","reason":"..."}` once per turn (guarded by the
  `stopHookActive` flag). ZCode caps Stop continuations at 3 natively.

## Why there is no `.zcode/config.json` here

The ZCode client UI and official docs support workspace-scope hooks in
`.zcode/config.json`, but the agent runtime on this machine (v2.1.0, WSL server)
**strips them unconditionally** — a "security policy" warning
(`config_project_hooks.ignored`) is logged and no hook runs. Only hooks in the
**user-level** `~/.zcode/cli/config.json` are executed (verified in source and
by log evidence).

The user-level config therefore points at these scripts via
`${ZCODE_PROJECT_DIR}` and guards on file existence, so other workspaces without
this directory are unaffected. Changing the runtime behavior would require a
ZCode update that honors workspace hooks.
