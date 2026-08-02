#!/usr/bin/env python3
"""Validate that tree_comments.__version__ is a valid PEP 440 version string.

This guards the single source of truth: ``tree_comments/__init__.py`` exposes
``__version__``, which hatchling reads dynamically at build time. A typo there
would only surface as a broken ``uv build`` at release time; this script fails
fast in pre-commit / CI instead.

Pure-stdlib (no ``packaging`` dependency) so it runs in any environment.

Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Authoritative PEP 440 regex, adapted from
# https://peps.python.org/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""


def main() -> int:
    init_path = Path("tree_comments/__init__.py")
    content = init_path.read_text(encoding="utf-8")

    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if match is None:
        print(
            f'error: could not find `__version__ = "..."` in {init_path}',
            file=sys.stderr,
        )
        return 1

    version = match.group(1)
    pep440_re = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE)
    if pep440_re.match(version) is None:
        print(
            f"error: {init_path} __version__ = {version!r} is not a valid PEP 440 version",
            file=sys.stderr,
        )
        return 1

    print(f"ok: {init_path} __version__ = {version!r} is valid PEP 440")
    return 0


if __name__ == "__main__":
    sys.exit(main())
