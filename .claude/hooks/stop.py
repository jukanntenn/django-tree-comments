#!/usr/bin/env python3
# Claude Stop: full-tree gate delegated to prek (the lint + check groups).
# prek is the single source of truth; this adapter only translates prek's exit
# code into Claude's block decision. Fires once per turn (stop_hook_active
# guard).
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GATE = ["uv", "run", "prek", "run", "--group", "lint", "--group", "check", "--all-files"]

# Generous vs. the subprocess timeout below; must stay under the Stop timeout
# (180s) configured in .claude/settings.json.
SUBPROCESS_TIMEOUT = 150

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
            timeout=SUBPROCESS_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        print("[stop-hook] uv not found on PATH; skipping lint gate", file=sys.stderr)
        return
    except subprocess.TimeoutExpired:
        print(
            f"[stop-hook] prek gate exceeded {SUBPROCESS_TIMEOUT}s and was skipped; "
            f"run `{GATE[2]}` manually to verify before pushing",
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
