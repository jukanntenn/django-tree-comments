"""Collection orchestration: combines timing/query/explain/redflags/memory into a
unified per-scenario metrics dict.

Corresponds to the element schema of report.json in the plan's design.md.

Design points (based on verified facts):
  - timing is passed in from the outside (pytest-benchmark's benchmark.stats),
    because tracemalloc slows things down by 3.3x; timing must be collected without tracemalloc enabled.
  - query/explain/memory are each collected in their own `with` block (capture_queries/measure_memory).
  - redflags are extracted from the explain result.
  - PG has additional postgres_extras (recursive iterations / buffer hit ratio), mined from ExplainResult.
"""

from __future__ import annotations

import datetime
import subprocess
from typing import Any

from django.db import connection

from perf.metrics.explain import ExplainResult, explain
from perf.metrics.memory import measure_memory
from perf.metrics.query_counter import capture_queries
from perf.metrics.redflags import extract_red_flags


def _git_commit() -> str:
    """Get the current git commit (for report archiving). Returns 'unknown' on failure."""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        )
    except Exception:
        return "unknown"


def _db_version() -> str:
    """Get the database version string."""
    try:
        with connection.cursor() as c:
            vendor = connection.vendor
            if vendor == "sqlite":
                c.execute("SELECT sqlite_version()")
            elif vendor == "postgresql":
                c.execute("SELECT version()")
            else:
                c.execute("SELECT VERSION()")
            return str(c.fetchone()[0])
    except Exception:
        return "unknown"


def _extract_pg_extras(explain_result: ExplainResult) -> dict[str, Any]:
    """Extract additional diagnostic metrics from a PG execution plan (recursive iterations / buffer hit ratio).

    From the PG JSON node tree:
      - recursive iterations: Actual Loops of the Recursive Union node
      - buffer hit ratio: (Shared Hit Blocks) / (Shared Hit + Read Blocks) * 100
    """
    extras: dict[str, Any] = {}
    raw = explain_result.raw
    if not raw or not isinstance(raw, list) or not raw:
        return extras
    plan = raw[0].get("Plan")
    if not plan:
        return extras

    total_hit = 0
    total_read = 0
    recursion_loops = None

    def walk(node):
        nonlocal total_hit, total_read, recursion_loops
        total_hit += node.get("Shared Hit Blocks", 0) or 0
        total_read += node.get("Shared Read Blocks", 0) or 0
        if node.get("Node Type") == "Recursive Union":
            recursion_loops = node.get("Actual Loops")
        for ch in node.get("Plans", []):
            walk(ch)

    walk(plan)

    if recursion_loops is not None:
        extras["recursion_iterations"] = recursion_loops
    if total_hit + total_read > 0:
        extras["shared_buffers_hit_pct"] = round(total_hit / (total_hit + total_read) * 100, 1)

    return extras


def collect_scenario_metrics(
    scenario,
    queryset_factory,
    timing_stats: dict | None = None,
) -> dict[str, Any]:
    """Collect all metrics for a scenario and return a dict matching the report.json element schema.

    Args:
        scenario:          a perf.scenarios.Scenario instance
        queryset_factory:  a zero-arg callable returning the queryset under test
                           (each call yields a fresh queryset)
        timing_stats:      timing dict extracted from pytest-benchmark's benchmark.stats.
                           When None, the timing field is left empty (a manual run may have no benchmark).
    """
    # 1. Query count + N+1 (wrap one real execution in capture_queries)
    with capture_queries() as qcap:
        list(queryset_factory())
    query_stats = qcap["stats"]

    # 2. Execution plan + red flags
    explain_result = explain(queryset_factory())
    redflag_result = extract_red_flags(explain_result)

    # 3. Peak memory (separate `with` block to avoid mixing with timing measurement)
    with measure_memory() as mcap:
        list(queryset_factory())
    memory_stats = mcap["stats"]

    # 4. PG extra metrics
    postgres_extras = {}
    if connection.vendor == "postgresql":
        postgres_extras = _extract_pg_extras(explain_result)

    # Combine into the unified schema
    return {
        "benchmark_id": scenario.id,
        "git_commit": _git_commit(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "db": {
            "backend": connection.vendor,
            "version": _db_version(),
        },
        "scenario": {
            "tree_shape": scenario.shape,
            "depth": scenario.depth,
            "fanout": scenario.fanout,
            "total_nodes": scenario.total,
            "scale": scenario.scale,
            "kind": scenario.kind,
        },
        "timing": timing_stats or {},
        "query": {
            "total_queries": query_stats.total_queries,
            "distinct_templates": query_stats.distinct_templates,
            "n_plus_one_suspected": query_stats.n_plus_one_suspected,
            "most_repeated_count": query_stats.most_repeated_count,
            "total_time_sec": round(query_stats.total_time_sec, 6),
        },
        "plan": {
            "raw_explain": explain_result.raw_text,
            "red_flags": redflag_result.to_dict(),
        },
        "postgres_extras": postgres_extras,
        "resources": memory_stats.to_dict(),
    }


def extract_timing_from_benchmark(benchmark) -> dict:
    """Extract timing statistics from the pytest-benchmark benchmark object.

    pytest-benchmark 5.2.3: benchmark.stats is Metadata, and benchmark.stats.stats is Stats.
    Stats are accessed via direct attribute access (s.median), Metadata via .get(). Here we
    uniformly take values from Stats. Stats.fields (stats.py:17-35) include min/median/q1/q3/iqr
    but no p95/p99, so those must be computed from data ourselves.
    """
    metadata = benchmark.stats  # Metadata
    # Metadata.stats is the actual Stats object
    stats = metadata.stats if hasattr(metadata, "stats") else metadata
    raw_data = list(stats.data) if hasattr(stats, "data") else []

    # numpy-free linear-interpolation percentile
    def pct(data, p):
        if not data:
            return None
        s = sorted(data)
        if len(s) == 1:
            return s[0]
        k = (len(s) - 1) * p
        f = int(k)
        c = min(f + 1, len(s) - 1)
        return s[f] + (s[c] - s[f]) * (k - f)

    def safe(attr):
        """Safely read an attribute from stats; return None if absent."""
        return getattr(stats, attr, None)

    result = {
        "min": safe("min"),
        "median": safe("median"),
        "q1": safe("q1"),
        "q3": safe("q3"),
        "iqr": safe("iqr"),
        "mean": safe("mean"),
        "stddev": safe("stddev"),
        "max": safe("max"),
        "rounds": safe("rounds"),
        "iterations": getattr(metadata, "iterations", None),
    }
    # Compute p95/p99 ourselves (not provided by pytest-benchmark)
    result["p95"] = pct(raw_data, 0.95)
    result["p99"] = pct(raw_data, 0.99)
    # Strip None values
    return {k: v for k, v in result.items() if v is not None}
