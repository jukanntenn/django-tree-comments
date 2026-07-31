"""Performance benchmark for the threaded query (threaded_for_instance).

threaded_for_instance is the actual entry point called when rendering the comment
tree (used by the templatetags), and includes the ordering
ORDER BY root_id DESC, submit_date, id. The difference from cte_for_instance is the ordering.
"""

import pytest

from tree_comments.models import Comment

from .conftest import collect_metrics_for


@pytest.mark.perf
@pytest.mark.django_db
def test_threaded_for_instance(benchmark, populated_tree, scenario):
    """Benchmark the threaded_for_instance query (with ordering)."""
    target = populated_tree

    def run():
        return list(Comment.objects.threaded_for_instance(target))

    # Timing measurement
    benchmark(run)

    # Collect the remaining metrics + aggregate
    collect_metrics_for(
        scenario,
        queryset_factory=lambda: Comment.objects.threaded_for_instance(target),
        benchmark=benchmark,
        query_name="threaded",
    )
