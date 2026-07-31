"""Four-category red-flag extractor (extracts structured performance signals from an ExplainResult).

The four red-flag categories (finalized in the plan; criteria based on three-DB EXPLAIN
measurement + source verification):

  (1) seq_scan_large_table  full table scan on a large table
     PG:    Node Type == "Seq Scan" and Actual Rows > threshold
     MySQL: TRADITIONAL type == "ALL"
     SQLite: detail starts with "SCAN" (a small table without USING COVERING/AUTOMATIC INDEX)
  (2) estimation_off        large row-count estimation deviation (PG/MySQL; not available on SQLite)
     PG:    |Plan Rows - Actual Rows| / Actual Rows > 0.5 and Actual Rows > 100
     MySQL: TREE-format estimated rows vs actual rows
  (3) spilled_to_disk       sort/intermediate result spilled to disk
     PG:    Sort Method contains "external merge" or Sort Space Type == "Disk"
            or Temp Read/Written Blocks > 0
     MySQL: TRADITIONAL Extra contains "Using filesort"
     SQLite: detail contains "USE TEMP B-TREE"
  (4) recursive_bulk        large recursive intermediate result (downgraded proxy)
     PG:    Recursive Union Actual Loops (iteration rounds) + WorkTable Scan Actual Rows
     MySQL: "Materialize recursive CTE" loops + "Scan new records" rows
     SQLite: "RECURSIVE STEP" subtree + SCAN count (SQLite has no precise metric; uses a proxy)

Default thresholds (tunable):
  SEQ_SCAN_MIN_ROWS = 1000    # Actual Rows above this counts as a "large table"
  ESTIMATION_RATIO  = 0.5     # deviation ratio above this is reported
  ESTIMATION_MIN_ROWS = 100   # not reported when actual row count is too small (small-sample estimation is meaningless)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from perf.metrics.explain import ExplainResult

# Thresholds
SEQ_SCAN_MIN_ROWS = 1000
ESTIMATION_RATIO = 0.5
ESTIMATION_MIN_ROWS = 100

# Slow-node threshold: execution-plan nodes whose Actual Total Time exceeds this value
# (in milliseconds) are reported as a red flag.
# Used to capture "abnormally slow nodes" that the red-flag system would otherwise miss
# (e.g. the Sort in the threaded query taking 62 seconds).
# Only PG has this metric (Actual Total Time from EXPLAIN ANALYZE).
SLOW_NODE_MS = 1000

# Type identifiers for the five red-flag categories
FLAG_SEQ_SCAN = "seq_scan_large_table"
FLAG_ESTIMATION = "estimation_off"
FLAG_SPILLED = "spilled_to_disk"
FLAG_RECURSIVE = "recursive_bulk"
FLAG_SLOW_NODE = "slow_node"


@dataclass
class RedFlag:
    """A single red flag."""

    type: str  # one of the five identifiers
    detail: str  # human/LLM-readable specific description
    severity: str = "warning"  # "warning" | "info"
    # Quantitative metric (for cross-scenario comparison; optional)
    metric: float | None = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "detail": self.detail,
            "severity": self.severity,
            "metric": self.metric,
        }


@dataclass
class RedFlagResult:
    """All red flags for one scenario."""

    flags: list[RedFlag] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.flags)

    @property
    def types(self) -> list[str]:
        return [f.type for f in self.flags]

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "types": self.types,
            "flags": [f.to_dict() for f in self.flags],
        }


def extract_red_flags(explain_result: ExplainResult) -> RedFlagResult:
    """Extract the four red-flag categories from an ExplainResult. Dispatches by backend."""
    backend = explain_result.backend
    if backend == "postgresql":
        return _extract_postgres(explain_result)
    if backend == "mysql":
        return _extract_mysql(explain_result)
    if backend == "sqlite":
        return _extract_sqlite(explain_result)
    return RedFlagResult()


# ---------------------------------------------------------------------------
# PostgreSQL: parse the FORMAT JSON node tree
# ---------------------------------------------------------------------------


def _extract_postgres(result: ExplainResult) -> RedFlagResult:
    flags = RedFlagResult()
    raw = result.raw
    if not raw or not isinstance(raw, list) or not raw:
        return flags
    plan = raw[0].get("Plan")
    if not plan:
        return flags

    # Collect diagnostic info for each kind of node
    seq_scans = []  # [(actual_rows, relation)]
    sort_spilled = []  # [dict]
    recursive_info = []  # [(loops, worktable_rows)]
    estimation_issues = []  # [(plan_rows, actual_rows, node_type)]
    slow_nodes = []  # [(node_type, actual_time_ms, rows, loops)]

    def walk(node):
        nt = node.get("Node Type", "")
        plan_rows = node.get("Plan Rows")
        actual_rows = node.get("Actual Rows")

        # (1) Seq Scan
        if nt == "Seq Scan":
            ar = actual_rows or 0
            seq_scans.append((ar, node.get("Relation Name", "?")))

        # (2) Estimation deviation (check every node that has Plan Rows/Actual Rows)
        if (
            isinstance(plan_rows, (int, float))
            and isinstance(actual_rows, (int, float))
            and actual_rows > ESTIMATION_MIN_ROWS
        ):
            ratio = abs(plan_rows - actual_rows) / actual_rows
            if ratio > ESTIMATION_RATIO:
                estimation_issues.append((plan_rows, actual_rows, nt))

        # (5) Slow node: Actual Total Time exceeds threshold (captures abnormally slow nodes otherwise missed)
        actual_time = node.get("Actual Total Time")
        if isinstance(actual_time, (int, float)) and actual_time > SLOW_NODE_MS:
            slow_nodes.append((nt, actual_time, actual_rows, node.get("Actual Loops", 0)))

        # (3) Sort spilled to disk
        if nt == "Sort":
            method = node.get("Sort Method", "")
            space_type = node.get("Sort Space Type", "")
            if "external merge" in method or space_type == "Disk":
                sort_spilled.append(
                    {
                        "method": method,
                        "space_type": space_type,
                        "space_used": node.get("Sort Space Used", 0),
                    }
                )
        # Temp blocks (intermediate result spilled to disk)
        temp_read = node.get("Temp Read Blocks", 0) or 0
        temp_written = node.get("Temp Written Blocks", 0) or 0
        if temp_read > 0 or temp_written > 0:
            sort_spilled.append({"node": nt, "temp_read": temp_read, "temp_written": temp_written})

        # (4) Recursive structure: Recursive Union node
        if nt == "Recursive Union":
            loops = node.get("Actual Loops", 0) or 0
            # Find the WorkTable Scan among child nodes
            wt_rows = 0
            for child in node.get("Plans", []):
                if child.get("Node Type") == "WorkTable Scan":
                    wt_rows = child.get("Actual Rows", 0) or 0
            recursive_info.append((loops, wt_rows))

        for child in node.get("Plans", []):
            walk(child)

    walk(plan)

    # Generate red flags
    for ar, rel in seq_scans:
        if ar > SEQ_SCAN_MIN_ROWS:
            flags.flags.append(
                RedFlag(
                    type=FLAG_SEQ_SCAN,
                    detail=f"Seq Scan on {rel} with Actual Rows={ar} (> {SEQ_SCAN_MIN_ROWS})",
                    metric=float(ar),
                )
            )

    for plan_r, actual_r, nt in estimation_issues:
        ratio = abs(plan_r - actual_r) / actual_r
        # Estimation deviation is universally inaccurate on recursive CTEs (a known CTE
        # characteristic); per-node reporting would drown out the signal.
        # Deduplicate by Node Type: keep only the largest deviation per type.
        # (estimation_issues is already in traversal order; aggregated here directly)
        flags.flags.append(
            RedFlag(
                type=FLAG_ESTIMATION,
                detail=f"{nt}: Plan Rows={plan_r} vs Actual Rows={actual_r} (deviation {ratio:.1%})",
                metric=round(ratio, 3),
            )
        )

    # Deduplicate estimation deviations: keep only the largest per Node Type
    seen_types = {}
    deduped = []
    for f in flags.flags:
        if f.type == FLAG_ESTIMATION:
            # Extract the Node Type from detail (the "Sort" of "Sort: ...")
            nt_key = f.detail.split(":")[0]
            if nt_key not in seen_types or f.metric > seen_types[nt_key].metric:
                seen_types[nt_key] = f
        else:
            deduped.append(f)
    flags.flags = deduped + list(seen_types.values())

    for s in sort_spilled:
        if "method" in s:
            flags.flags.append(
                RedFlag(
                    type=FLAG_SPILLED,
                    detail=f"Sort spilled: method={s['method']}, space_type={s['space_type']}, used={s['space_used']}kB",
                    severity="warning",
                    metric=float(s.get("space_used", 0)),
                )
            )
        else:
            flags.flags.append(
                RedFlag(
                    type=FLAG_SPILLED,
                    detail=f"{s['node']} read/wrote temp blocks: temp_read={s['temp_read']}, temp_written={s['temp_written']}",
                    metric=float(s["temp_read"] + s["temp_written"]),
                )
            )

    for loops, wt_rows in recursive_info:
        # Proxy signal: many iterations or a large worktable per round counts as large recursion bulk
        if loops > 10 or wt_rows > SEQ_SCAN_MIN_ROWS:
            flags.flags.append(
                RedFlag(
                    type=FLAG_RECURSIVE,
                    detail=f"Recursive Union: {loops} iterations, WorkTable avg {wt_rows} rows/round",
                    severity="info",
                    metric=float(loops * wt_rows),
                )
            )

    # (5) Slow nodes: sorted by elapsed time descending, at most 5 reported (to avoid noise)
    # Note Actual Total Time is cumulative (includes children), so it may overlap; the goal is
    # to expose slow nodes to the LLM
    for nt, t_ms, rows, loops in sorted(slow_nodes, key=lambda x: -x[1])[:5]:
        flags.flags.append(
            RedFlag(
                type=FLAG_SLOW_NODE,
                detail=f"{nt}: Actual Total Time={t_ms:.0f}ms (> {SLOW_NODE_MS}ms), rows={rows}, loops={loops}",
                severity="warning",
                metric=float(t_ms),
            )
        )

    return flags


# ---------------------------------------------------------------------------
# MySQL: parse TREE text + TRADITIONAL table
# ---------------------------------------------------------------------------

# Capture (actual ... rows=R ... loops=N) from the TREE format
_MYSQL_ACTUAL_RE = re.compile(r"actual time=([\d.]+)\.\.([\d.]+)\s+rows=([\d.]+)\s+loops=(\d+)")
# Estimated (cost=... rows=R) from the TREE format
_MYSQL_EST_RE = re.compile(r"rows=([\d.]+)")


def _extract_mysql(result: ExplainResult) -> RedFlagResult:
    flags = RedFlagResult()
    raw = result.raw
    if not raw or not isinstance(raw, dict):
        return flags
    tree = raw.get("tree", "")
    traditional = raw.get("traditional", [])

    # (1) + (3) extracted from the TRADITIONAL table
    for row in traditional:
        row_type = (row.get("type") or "").lower()
        extra = row.get("Extra") or ""
        # (1) Full table scan: MySQL type=ALL is not always a large table
        # (a full scan is faster for small tables); only report a red flag when the
        # estimated rows exceed the threshold.
        if row_type == "all":
            rows = row.get("rows", 0) or 0
            if rows and rows > SEQ_SCAN_MIN_ROWS:
                flags.flags.append(
                    RedFlag(
                        type=FLAG_SEQ_SCAN,
                        detail=f"MySQL type=ALL (full table scan), estimated rows={rows}",
                        metric=float(rows),
                    )
                )
        # (3) filesort
        if "Using filesort" in extra:
            flags.flags.append(RedFlag(type=FLAG_SPILLED, detail=f"MySQL Extra: {extra.strip()}"))

    # (2) Estimation deviation + (4) recursion extracted from the TREE text
    # Find the actual rows/loops of the "Materialize recursive CTE" row and Scan new records
    for line in tree.split("\n"):
        if "Materialize recursive CTE" in line:
            m = _MYSQL_ACTUAL_RE.search(line)
            if m:
                rows = float(m.group(3))
                loops = float(m.group(4))
                if loops > 10 or rows > SEQ_SCAN_MIN_ROWS:
                    flags.flags.append(
                        RedFlag(
                            type=FLAG_RECURSIVE,
                            detail=f"Materialize recursive CTE: {loops} iterations, avg {rows} rows/round",
                            severity="info",
                            metric=loops * rows,
                        )
                    )

    return flags


# ---------------------------------------------------------------------------
# SQLite: parse EQP detail rows
# ---------------------------------------------------------------------------


def _extract_sqlite(result: ExplainResult) -> RedFlagResult:
    flags = RedFlagResult()
    raw = result.raw
    if not raw or not isinstance(raw, dict):
        return flags
    details = raw.get("query_plan", [])

    # SQLite has no row-count estimates; judgments are text-based only
    # (1) SCAN (full scan of a small table without an automatic index)
    # (3) USE TEMP B-TREE
    # (4) presence of RECURSIVE STEP is recorded (proxy)
    has_recursive = False
    for detail in details:
        d = detail.strip()
        # (3) Spilled to disk
        if "USE TEMP B-TREE" in d:
            flags.flags.append(RedFlag(type=FLAG_SPILLED, detail=f"SQLite: {d}"))
        # (4) Recursive structure present
        if "RECURSIVE STEP" in d:
            has_recursive = True
        # (1) SCAN (exclude SCANs on automatic/covering indexes, which are optimized)
        # True full table scan: "SCAN <table>" without USING INDEX
        if d.startswith("SCAN ") and "USING" not in d:
            flags.flags.append(
                RedFlag(
                    type=FLAG_SEQ_SCAN,
                    detail=f"SQLite: {d} (full table scan, no index)",
                    severity="warning",
                )
            )

    # (4) Recursion present (SQLite has no precise bulk metric; only presence is marked)
    if has_recursive:
        flags.flags.append(
            RedFlag(
                type=FLAG_RECURSIVE,
                detail="SQLite: RECURSIVE STEP present (no precise bulk metric; presence only)",
                severity="info",
            )
        )

    return flags
