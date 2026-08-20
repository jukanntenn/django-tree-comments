#!/usr/bin/env python3
"""Sync AI tool configs from their source of truth.

- ``AGENTS.md`` -> ``CLAUDE.md`` (Claude Code reads CLAUDE.md)
- ``.claude/skills/`` -> ``.agents/skills/`` and ``.zcode/skills/``
  (ZCode reads both; ``.claude/skills/`` is the single editable copy)

Run automatically by the prek ``agents-sync`` hook (format group) whenever
AGENTS.md or ``.claude/skills/`` changes, so the copies can never drift.

Pure stdlib; exits 0 on success.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sync_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        print(f"error: source {src} does not exist", file=sys.stderr)
        sys.exit(1)
    shutil.copy2(src, dst)
    print(f"Synced {dst.relative_to(ROOT)} <- {src.relative_to(ROOT)}")


def sync_dir(src: Path, dst: Path) -> None:
    if not src.is_dir():
        print(f"error: source {src} does not exist", file=sys.stderr)
        sys.exit(1)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Synced {dst.relative_to(ROOT)}/ <- {src.relative_to(ROOT)}/")


def main() -> int:
    sync_file(ROOT / "AGENTS.md", ROOT / "CLAUDE.md")
    for target in (".agents", ".zcode"):
        sync_dir(ROOT / ".claude" / "skills", ROOT / target / "skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
