#!/usr/bin/env python3
# ZCode PostToolUse (Edit|Write): delegate formatting to prek (the format
# group — the single source of truth). No formatter logic lives here, so this
# adapter can never drift from prek/CI.
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    file_path = (payload.get("toolInput") or {}).get("file_path")
    if not isinstance(file_path, str) or not (Path(file_path).is_file() or (ROOT / file_path).is_file()):
        return

    try:
        r = subprocess.run(
            ["uv", "run", "prek", "run", "--group", "format", "--files", file_path],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[zcode-post-tool-use] uv not found on PATH; skipped formatting", file=sys.stderr)
        return
    # exit 0 = clean, 1 = fixers modified files (expected for a formatter);
    # surface only real errors.
    if r.returncode not in (0, 1):
        print(f"[zcode-post-tool-use] prek format exited {r.returncode}:", file=sys.stderr)
        if r.stdout:
            print(r.stdout, file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
