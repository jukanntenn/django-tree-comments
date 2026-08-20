#!/usr/bin/env python3
# Codex PostToolUse (apply_patch): delegate formatting to prek (the format
# group — the single source of truth). No formatter logic lives here, so this
# adapter can never drift from prek/CI. Only the apply_patch text parsing is
# Codex-specific.
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MOVE_TO_PREFIX = "*** Move to: "
PATCH_FILE_PREFIXES = (
    "*** Update File: ",
    "*** Add File: ",
)


def extract_edited_paths(command: str) -> list[str]:
    paths: list[str] = []
    pending_update: str | None = None
    for raw_line in command.splitlines():
        line = raw_line.strip()
        if pending_update is not None and line.startswith(MOVE_TO_PREFIX):
            paths.append(line[len(MOVE_TO_PREFIX) :].strip())
            pending_update = None
            continue
        if pending_update is not None:
            paths.append(pending_update)
            pending_update = None
        if line.startswith(MOVE_TO_PREFIX):
            continue
        for prefix in PATCH_FILE_PREFIXES:
            if line.startswith(prefix):
                pending_update = line[len(prefix) :].strip()
                break
    if pending_update is not None:
        paths.append(pending_update)
    return paths


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return

    paths = [p for p in extract_edited_paths(command) if (ROOT / p).is_file()]
    if not paths:
        return

    try:
        r = subprocess.run(
            ["uv", "run", "prek", "run", "--group", "format", "--files", *paths],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[codex-post-tool-use] uv not found on PATH; skipped formatting", file=sys.stderr)
        return
    # exit 0 = clean, 1 = fixers modified files (expected for a formatter);
    # surface only real errors.
    if r.returncode not in (0, 1):
        print(f"[codex-post-tool-use] prek format exited {r.returncode}:", file=sys.stderr)
        if r.stdout:
            print(r.stdout, file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
