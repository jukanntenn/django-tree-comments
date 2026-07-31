"""Performance benchmark for the CTE query (cte_for_instance).

Per scenario:
  1. The benchmark measures timing (multiple warm rounds, tracemalloc disabled).
  2. Query/explain/redflags/memory are collected in a with block outside the benchmark.
  3. collect_metrics_for aggregates into the global pool, and a report is generated at sessionfinish.
"""

import pytest

from tree_comments.models import Comment

from .conftest import collect_metrics_for


@pytest.mark.perf
@pytest.mark.django_db
def test_cte_for_instance(benchmark, populated_tree, scenario):
    """Benchmark the cte_for_instance query."""
    target = populated_tree

    def run():
        return list(Comment.objects.cte_for_instance(target))

    # 1. Timing measurement (benchmark calls run only once)
    benchmark(run)

    # 2. Collect the remaining metrics + aggregate (pass the benchmark object to extract timing)
    collect_metrics_for(
        scenario,
        queryset_factory=lambda: Comment.objects.cte_for_instance(target),
        benchmark=benchmark,
    )
