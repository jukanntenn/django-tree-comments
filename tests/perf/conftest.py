"""conftest for the performance benchmark harness.

Responsibilities:
  1. Provide a populated_tree fixture parametrized by scenario (regenerated per test).
  2. Collect per-scenario metrics (query/explain/redflags/memory) into a global pool.
  3. pytest_sessionfinish hook: correlate benchmark timings with collected metrics
     and generate report.json + report.md.

Why timings and metrics are collected separately (empirically verified):
  tracemalloc slows queries down by ~3.3x, so the benchmark (which measures timing)
  invokes the function under test only once; the other metrics (query/explain/memory)
  are gathered separately inside a with block outside the benchmark. This is exactly
  the design of perf/metrics/collector.collect_scenario_metrics.
"""

from __future__ import annotations

import os

import pytest
from django.contrib.auth import get_user_model

from perf.factories import build_comment_tree
from perf.scenarios import ALL_SCENARIOS, Scenario
from tree_comments.models import Comment

User = get_user_model()

# Global results pool: key = query_name:scenario_id -> metrics dict
_collected_metrics: dict[str, dict] = {}
# Session-fixed output directory (determined when the first report is written,
# so all incremental writes land in the same directory)
_output_dir: str | None = None


def _current_backend() -> str:
    """The database backend the current test run is using (read from env var)."""
    return os.environ.get("TREE_COMMENTS_DB_BACKEND", "sqlite").lower()


# Compute scenarios for the current backend at module load (fixture params must be
# fixed at definition time, hence this runs before the fixture is defined)
def _scenarios_for_current_backend():
    backend = _current_backend()
    return [s for s in ALL_SCENARIOS if s.backend == backend]


def pytest_configure(config):
    """Register the perf marker (avoids marker warnings)."""
    config.addinivalue_line("markers", "perf: performance benchmark test")


def pytest_collection_modifyitems(config, items):
    """Skip perf tests by default (they are slow), unless the perf path or -m perf is given explicitly.

    This way a plain `pytest` does not run benchmarks; only `pytest tests/perf/` or `-m perf` does.
    """
    if config.getoption("-m") == "perf":
        return
    # If the tests/perf path was not given on the command line, skip perf tests
    perf_paths = ("tests/perf/", "tests" + os.sep + "perf")
    args = config.getoption("file_or_dir", default=[])
    running_perf = any(p.startswith(perf_paths) for p in args)
    if not running_perf:
        skip_perf = pytest.mark.skip(reason="perf benchmark, run with: pytest tests/perf/")
        for item in items:
            if "perf" in item.keywords or item.fspath.strpath.replace("\\", "/").find("tests/perf/") >= 0:
                item.add_marker(skip_perf)


@pytest.fixture(params=_scenarios_for_current_backend(), ids=lambda s: s.id)
def scenario(request) -> Scenario:
    """Parametrized injection of scenarios for the current backend."""
    return request.param


@pytest.fixture
def populated_tree(request, db, scenario):
    """Generate a comment tree for each scenario. scope=function (regenerated per test).

    Returns (target_object, queryset_factory).
    queryset_factory is a zero-argument callable that returns a fresh queryset under test on each call.
    """
    from django.db import connection

    from tests.app.models import Post

    user = User.objects.first()
    if user is None:
        user = User.objects.create_user("perfuser")
    target = Post.objects.create(title=f"perf-{scenario.id}", author=user)

    build_comment_tree(
        target,
        shape=scenario.shape,
        depth=scenario.depth,
        fanout=scenario.fanout,
        total=scenario.total,
        seed=42,
    )

    # ANALYZE is only needed on PG: cost estimation of the outer JOIN in PG's recursive
    # CTE depends on table statistics (costsize.c:1887 hard-codes "assume 10 iterations",
    # but rterm->rows comes from table statistics). After a bulk insert autovacuum has not
    # run yet -> stale statistics -> the optimizer picks Nested Loop + WorkTable rescans
    # (loops=210000), and the measured time jumps from ~220ms to ~48s (220x). MySQL's
    # FollowTailIterator and SQLite's co-routine are structurally immune to this issue;
    # empirical verification showed the plan was identical before and after ANALYZE, so
    # only PG runs it.
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(f"ANALYZE {connection.ops.quote_name(Comment._meta.db_table)}")

    # The target is freshly created, so there are no old comments to clear for it
    return target


def collect_metrics_for(scenario: Scenario, queryset_factory, benchmark=None, query_name="cte"):
    """Collect all metrics for a scenario and add them to the global pool.

    query_name distinguishes different queries under test (cte / threaded) so the
    same scenario does not get overwritten. When benchmark is not None, timing is
    extracted from it; otherwise timing is left empty (filled in at sessionfinish).
    """
    from perf.metrics.collector import (
        collect_scenario_metrics,
        extract_timing_from_benchmark,
    )

    timing = extract_timing_from_benchmark(benchmark) if benchmark is not None else None
    metrics = collect_scenario_metrics(scenario, queryset_factory, timing)
    # Prefix benchmark_id with query_name so cte/threaded do not overwrite each other
    metrics["benchmark_id"] = f"{query_name}/{scenario.id}"
    metrics["query_name"] = query_name
    key = f"{query_name}:{scenario.id}"
    _collected_metrics[key] = metrics
    # Incremental report writing: flush after each completed scenario so an
    # interrupted session still keeps the finished results
    _write_reports(final=False)
    return metrics


def pytest_sessionfinish(session, exitstatus):
    """At end of session: write the final report once (to ensure completeness).

    Timing was already extracted synchronously in collect_metrics_for (the in-test
    benchmark has already run) and incremental writes have already flushed.
    Here final=True prints a completion notice.
    """
    if not _collected_metrics:
        return
    _write_reports(final=True)


def _write_reports(final: bool = False):
    """Generate report.json + report.md, archived under perf/reports/<commit>-<timestamp>/.

    The output directory is fixed on the first call (session-scoped) so all
    incremental writes land in the same directory. When final=True, print a
    completion notice (only called from sessionfinish).
    """
    global _output_dir
    import datetime
    import subprocess

    from perf.reporting.json_reporter import write_json_report
    from perf.reporting.markdown_reporter import write_markdown_report

    if _output_dir is None:
        try:
            commit = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
        except Exception:
            commit = "unknown"
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        _output_dir = os.path.join("perf", "reports", f"{commit}-{ts}")

    os.makedirs(_output_dir, exist_ok=True)
    metrics_list = list(_collected_metrics.values())
    json_path = os.path.join(_output_dir, "report.json")
    md_path = os.path.join(_output_dir, "report.md")
    write_json_report(metrics_list, json_path)
    write_markdown_report(metrics_list, md_path)

    if final:
        print(f"\n[perf] Reports generated ({len(metrics_list)} scenarios):\n  {json_path}\n  {md_path}\n")
