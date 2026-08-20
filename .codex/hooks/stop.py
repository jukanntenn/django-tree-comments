#!/usr/bin/env python3
# Codex Stop: full-tree gate delegated to prek (the lint + check groups).
# prek is the single source of truth; this adapter only translates prek's exit
# code into Codex's block decision. Fires once per turn (stop_hook_active
# guard).
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GATE = ["uv", "run", "prek", "run", "--group", "lint", "--group", "check", "--all-files"]

REASON_TEMPLATE = """The prek lint/check gate found issues it could not auto-fix. Resolve them before finishing.

Diagnostics:
<gate_output>
{diagnostics}
</gate_output>

Required:
1. Fix every diagnostic above with a real code change. Do not silence
   them with `# noqa`, inline rule disables, or `type: ignore` — only
   treat a diagnostic as a false positive if you can justify why.
2. After editing, run `uv run prek run --group lint --group check --all-files`
   yourself to verify the gate passes.
3. Only attempt to finish again once that command exits 0.

This enforcement fires once per turn — the stop hook will not block a
second time. If you stop again with errors remaining, they will slip
through to CI. Verify before you finish."""


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    if payload.get("stop_hook_active"):
        return

    try:
        r = subprocess.run(
            GATE,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=150,
            check=False,
        )
    except FileNotFoundError:
        print("[codex-stop-hook] uv not found on PATH; skipping lint gate", file=sys.stderr)
        return
    except subprocess.TimeoutExpired:
        print(
            "[codex-stop-hook] prek gate exceeded 150s and was skipped; "
            "run `prek run --group lint --group check --all-files` manually to verify",
            file=sys.stderr,
        )
        return

    if r.returncode != 0:
        diagnostics = "\n".join(line for line in (r.stdout + r.stderr).splitlines() if line.strip())
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": REASON_TEMPLATE.format(diagnostics=diagnostics),
                }
            )
        )


if __name__ == "__main__":
    main()
    sys.exit(0)
