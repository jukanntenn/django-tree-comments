#!/usr/bin/env python3
"""Fail if the committed migrations are out of date with the models.

Wraps ``makemigrations --check --dry-run`` (the same gate CI used to run in
migrations.yml) so model/migration drift is caught locally by the prek
``migrations-drift`` hook (check group) instead of only on a push.

Exits 0 when no migration is pending, 1 otherwise.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    os.chdir(ROOT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    import django
    from django.core.management import call_command

    django.setup()
    try:
        call_command("makemigrations", "--check", "--dry-run")
    except SystemExit as exc:
        # makemigrations --check calls sys.exit(1) when migrations are pending.
        if exc.code != 0:
            print(
                "error: model changes without a migration detected — run "
                "`uv run python manage.py makemigrations tree_comments` "
                "(manage.py is in examples/default/)",
                file=sys.stderr,
            )
            return 1
        raise
    print("ok: migrations are in sync with the models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
