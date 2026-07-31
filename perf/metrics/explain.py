"""Execution-plan collector (unified cross-backend interface).

Dispatches by connection.vendor to each backend's EXPLAIN implementation and returns
a unified ExplainResult.

Fact basis (real EXPLAIN output measured across the three DBs + source verification):
  - PostgreSQL: EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) returns a single-row, single-column JSON string.
    The node tree contains Node Type / Plan Rows / Actual Rows / Sort Method / Shared Hit/Read Blocks.
    Recursive CTE nodes: Recursive Union / WorkTable Scan / CTE Scan.
  - MySQL: must run twice.
      * EXPLAIN ANALYZE (TREE format): an indented tree, with (actual time=.. rows=.. loops=..);
        recursive nodes are Materialize recursive CTE / Repeat until convergence / Scan new records.
      * EXPLAIN (TRADITIONAL): table columns; Extra contains "Using filesort" / "Using temporary",
        and type=ALL indicates a full table scan. In TREE format these signals are child nodes
        and inconvenient to parse, hence the dual format.
  - SQLite: EXPLAIN QUERY PLAN returns 4 columns (id, parent, notused, detail);
    detail contains SCAN / SEARCH / CO-ROUTINE / SETUP / RECURSIVE STEP / USE TEMP B-TREE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from django.db import connection


@dataclass
class ExplainResult:
    """Execution-plan collection result (unified across backends)."""

    backend: str
    # Raw execution plan: for PG a parsed JSON dict; for MySQL {"tree": str, "traditional": list};
    # for SQLite a list of detail rows. Serialized back to its native shape when reported.
    raw: Any = None
    # Full human-readable execution plan text (for report archiving and LLM reference)
    raw_text: str = ""

    def to_dict(self) -> dict:
        """Serialize to a report dict. raw keeps its backend-native structure."""
        return {
            "backend": self.backend,
            "raw": self.raw,
            "raw_text": self.raw_text,
        }


def explain(queryset) -> ExplainResult:
    """Collect the execution plan of a queryset.

    Dispatches by connection.vendor to each backend's implementation. Actually executes the query (ANALYZE mode).
    """
    sql, params = queryset.query.sql_with_params()
    vendor = connection.vendor

    if vendor == "postgresql":
        return _explain_postgres(sql, params)
    if vendor == "mysql":
        return _explain_mysql(sql, params)
    if vendor == "sqlite":
        return _explain_sqlite(sql, params)
    # Unknown backend: fall back to storing only the SQL, do not run EXPLAIN
    return ExplainResult(backend=vendor, raw=None, raw_text=f"(unsupported backend: {vendor})")


def _explain_postgres(sql: str, params: tuple) -> ExplainResult:
    """PostgreSQL: EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON).

    Returns the parsed JSON (a list whose first element contains Plan/Execution Time, etc.).
    raw_text stores pretty-printed JSON for readability.
    """
    explain_sql = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql
    with connection.cursor() as cursor:
        cursor.execute(explain_sql, params)
        rows = cursor.fetchall()
    # FORMAT JSON returns a single row and column whose value is a JSON string
    # (psycopg auto-parses it into a list/dict)
    plan_data = rows[0][0]
    if isinstance(plan_data, str):
        plan_data = json.loads(plan_data)

    return ExplainResult(
        backend="postgresql",
        raw=plan_data,
        raw_text=json.dumps(plan_data, indent=2, ensure_ascii=False),
    )


def _explain_mysql(sql: str, params: tuple) -> ExplainResult:
    """MySQL: dual-format collection.

    TREE format (EXPLAIN ANALYZE): get recursive / actual execution statistics.
    TRADITIONAL format (EXPLAIN): get type=ALL / Using filesort / Using temporary.
    """
    tree_text = ""
    traditional_rows: list[dict[str, Any]] = []

    # TREE format: a single text column per row
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN ANALYZE " + sql, params)
        rows = cursor.fetchall()
    tree_lines = [str(row[0]) for row in rows]
    tree_text = "\n".join(tree_lines)

    # TRADITIONAL format: multiple columns; column names taken from description
    # (mysqlclient's description elements are tuples)
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN " + sql, params)
        cols = [d[0] for d in cursor.description]
        for row in cursor.fetchall():
            traditional_rows.append(dict(zip(cols, row)))

    return ExplainResult(
        backend="mysql",
        raw={"tree": tree_text, "traditional": traditional_rows},
        raw_text="=== EXPLAIN ANALYZE (TREE) ===\n"
        + tree_text
        + "\n\n=== EXPLAIN (TRADITIONAL) ===\n"
        + "\n".join(str(r) for r in traditional_rows),
    )


def _explain_sqlite(sql: str, params: tuple) -> ExplainResult:
    """SQLite: EXPLAIN QUERY PLAN; returns a list of detail rows.

    Outputs 4 columns (id, parent, notused, detail); detail is the diagnostic text.
    """
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN QUERY PLAN " + sql, params)
        rows = cursor.fetchall()
    # rows: [(id, parent, notused, detail), ...]
    detail_lines = [row[3] for row in rows]

    return ExplainResult(
        backend="sqlite",
        raw={"query_plan": detail_lines},
        raw_text="\n".join(detail_lines),
    )
