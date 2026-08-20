#!/usr/bin/env python3
"""Validate the Conventional Commits format on the commit message subject line.

The prek commit-msg hook passes the commit message file path as argv[1].
Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"^(feat|fix|chore|docs|refactor|test|build|style|ci|perf|revert)"
    r"(\([^)]+\))?!?: .+"
)


def main() -> int:
    msg_file = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        msg = Path(msg_file).read_text(encoding="utf-8") if msg_file else sys.stdin.read()
    except OSError:
        msg = ""
    subject = msg.splitlines()[0] if msg.splitlines() else ""
    if not PATTERN.match(subject):
        print("ERROR: commit message must follow Conventional Commits.")
        print("  Expected: <type>(<scope>)?: <summary>")
        print("  Types: feat|fix|chore|docs|refactor|test|build|style|ci|perf|revert")
        print(f"  Got: {subject}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
