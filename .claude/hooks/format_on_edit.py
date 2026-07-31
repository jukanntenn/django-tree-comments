#!/usr/bin/env python3
"""PostToolUse hook: format the file the agent just edited, by extension.

Runs the appropriate formatter silently (--exit-zero / equivalent):
  .py / .pyi  -> ruff format + ruff check --fix --exit-zero
  .html       -> djlint --reformat
  .css .js .ts .jsx .tsx .json .yaml .yml .toml -> prettier --write

Non-matched extensions are skipped. uv / npx not on PATH -> silent skip.
Always exits 0: PostToolUse cannot block (tool already ran), and we don't
want to surface formatting noise. Remaining lint errors are caught by the
Stop hook.

Exit codes (Claude Code & Codex & ZCode identical):
  exit 0 = success (stdout parsed as JSON only on exit 0; we emit no JSON).
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys


def run(cmd: list[str]) -> None:
    with contextlib.suppress(FileNotFoundError):
        subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603


def main() -> None:
    try:
        hook = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    file_path = hook.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return

    if file_path.endswith((".py", ".pyi")):
        run(["uv", "run", "ruff", "format", file_path])
        run(["uv", "run", "ruff", "check", "--fix", "--exit-zero", file_path])
    elif file_path.endswith((".html", ".djhtml")):
        run(["uv", "run", "djlint", file_path, "--reformat"])
    elif file_path.endswith((".css", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml", ".toml")):
        run(["npx", "--no-install", "prettier", "--write", file_path])


if __name__ == "__main__":
    main()
    sys.exit(0)
