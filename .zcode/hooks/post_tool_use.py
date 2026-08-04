#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import PurePath


def commands_for(path: PurePath) -> list[list[str]]:
    match path.suffix:
        case ".py" | ".pyi":
            return [
                ["uv", "run", "ruff", "check", "--fix", str(path)],
                ["uv", "run", "ruff", "format", str(path)],
            ]
        case _:
            return []


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    raw_path = (payload.get("toolInput") or {}).get("file_path")
    if not isinstance(raw_path, str):
        return

    from_hook = PurePath(raw_path)

    try:
        for cmd in commands_for(from_hook):
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
            if result.returncode != 0:
                prefix = f"[zcode-post-tool-use] {cmd[3]}"
                for line in (result.stdout + result.stderr).splitlines():
                    if line.strip():
                        print(f"{prefix}: {line}", file=sys.stderr)
    except FileNotFoundError:
        print(f"[zcode-post-tool-use] uv not found on PATH; skipped {from_hook}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
