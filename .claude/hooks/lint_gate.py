#!/usr/bin/env python3
"""Stop hook: block the agent from stopping while lint/type errors remain.

Runs, in order:
  1. ruff check        (Python lint)
  2. djlint --lint     (Django template lint)
  3. tsc --noEmit      (e2e TypeScript typecheck, only if e2e/ exists)
  4. mypy --strict      (Python typecheck)

On the FIRST failure, blocks the stop with exit 0 + JSON:
  {"decision": "block", "reason": "<tool> failed:\n<output>"}

The `reason` is fed back to the agent as a continuation prompt (official
Claude Code / Codex / ZCode mechanism; exit 0 + JSON is the documented
structured-control form, preferred over exit 2 + stderr).

Infinite-loop guard: if stop_hook_active is true, allow stop (CI is the real gate).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def check(cmd: list[str], label: str) -> str | None:
    """Run cmd; return None if pass, else a reason string."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    except FileNotFoundError:
        return None  # tool missing -> skip, don't block
    if result.returncode == 0:
        return None
    out = (result.stdout + result.stderr).strip()
    return f"{label} failed — fix these before stopping:\n{out}"


def main() -> None:
    try:
        hook = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    # Agent already got one continuation pass: let it stop. CI is the real gate.
    if hook.get("stop_hook_active"):
        return

    checks: list[tuple[list[str], str]] = [
        (["uv", "run", "ruff", "check"], "ruff check"),
        (["uv", "run", "djlint", "tree_comments/templates", "--lint"], "djlint"),
        (["uv", "run", "mypy", "tree_comments"], "mypy"),
    ]
    # e2e TS typecheck only if e2e/ present
    e2e_dir = Path("e2e")
    if e2e_dir.is_dir() and (e2e_dir / "tsconfig.json").exists():
        tsc_bin = e2e_dir / "node_modules" / ".bin" / "tsc"
        if tsc_bin.exists():
            checks.append(([str(tsc_bin), "--noEmit", "-p", "e2e/tsconfig.json"], "tsc (e2e)"))

    for cmd, label in checks:
        reason = check(cmd, label)
        if reason:
            print(json.dumps({"decision": "block", "reason": reason}))
            return  # exit 0 + JSON


if __name__ == "__main__":
    main()
    sys.exit(0)
