"""Query counting and N+1 detection.

Leverages Django's connection.queries (recorded when force_debug_cursor=True) to capture
all SQL executed during a measurement window, and reports: total query count, number of
distinct SQL templates, suspected N+1, and total elapsed time.

Fact basis (measured + source):
  - With force_debug_cursor=True, queries are recorded regardless of settings.DEBUG
    (Django source db/backends/util.py: CursorDebugWrapper is enabled when force_debug_cursor
    or DEBUG=True).
  - connection.queries is a list[dict]; each dict has "sql" (the full text with parameters substituted)
    and "time" (a str in seconds, e.g. "0.001").
  - queries is not cleared automatically and accumulates; use reset_queries() to clear it.
  - time has limited precision on SQLite (often shows "0.000"), but N+1 detection primarily
    relies on counts and does not depend on per-query elapsed time.

N+1 detection principle:
  The sql in connection.queries is text with parameters substituted (e.g. WHERE "id" = 1).
  Normalizing numeric/string literals to placeholders yields a "template"; the same template
  appearing many times is a suspected N+1.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.db import connection, reset_queries

# Normalize SQL: treat numbers, single-quoted strings, and content outside double-quoted strings as parameters and replace them.
# Goal: normalize "WHERE id = 1" and "WHERE id = 2" to the same template.
_NUMBER_RE = re.compile(r"\b\d+\b")
_STRING_RE = re.compile(r"'(?:[^']|'')*'")


def _normalize_sql(sql: str) -> str:
    """Replace literal parameters in SQL with placeholders to obtain the query template.

    Example:
      SELECT ... WHERE "id" = 1 LIMIT 21
      -> SELECT ... WHERE "id" = ? LIMIT ?
    """
    s = _STRING_RE.sub("?", sql)
    s = _NUMBER_RE.sub("?", s)
    return s


# N+1 suspicion threshold: the same SQL template appearing more than this many times is judged an N+1.
# A CTE query is itself a single statement; normal rendering produces only a few distinct templates
# even with prefetch. The same template repeating more than 5 times is almost certainly an N+1
# (e.g. accessing related objects one row at a time).
N_PLUS_ONE_THRESHOLD = 5


@dataclass
class QueryStats:
    """Query statistics for a single measurement."""

    total_queries: int = 0
    # SQL template -> occurrence count
    template_counts: dict[str, int] = field(default_factory=dict)
    n_plus_one_suspected: bool = False
    # The most repeated template (when N+1 is suspected, this is the suspect query)
    most_repeated_template: str = ""
    most_repeated_count: int = 0
    # Total elapsed time (seconds, float). Limited precision on SQLite.
    total_time_sec: float = 0.0

    @property
    def distinct_templates(self) -> int:
        return len(self.template_counts)

    def to_dict(self) -> dict:
        """Serialize to a report-friendly dict (no full SQL text, only templates and counts)."""
        return {
            "total_queries": self.total_queries,
            "distinct_templates": self.distinct_templates,
            "n_plus_one_suspected": self.n_plus_one_suspected,
            "most_repeated_template": self.most_repeated_template[:300],
            "most_repeated_count": self.most_repeated_count,
            "total_time_sec": round(self.total_time_sec, 6),
        }


@contextmanager
def capture_queries():
    """Context manager: captures all queries within its block and returns QueryStats on exit.

    Usage:
        with capture_queries() as cap:
            list(Comment.objects.cte_for_instance(post))
        stats = cap.stats  # QueryStats

    Implementation: clears queries and forces the debug cursor on entry; restores on exit after tallying.
    """
    # Save the prior state so it is restored even on abnormal exit
    prev_force_debug = connection.force_debug_cursor
    reset_queries()
    connection.force_debug_cursor = True

    # Use a holder so the yielded value is accessible to the caller
    holder = {"stats": None}
    try:
        yield holder
        # Collect and tally
        queries: list[dict] = list(connection.queries)
        holder["stats"] = _analyze_queries(queries)
    finally:
        connection.force_debug_cursor = prev_force_debug
        reset_queries()


def _analyze_queries(queries: list[dict]) -> QueryStats:
    """Analyze the query list and produce QueryStats."""
    stats = QueryStats()
    stats.total_queries = len(queries)

    template_counts: dict[str, int] = {}
    for q in queries:
        sql = q.get("sql", "")
        template = _normalize_sql(sql)
        template_counts[template] = template_counts.get(template, 0) + 1
        # Accumulate elapsed time (time is a str in seconds)
        try:
            stats.total_time_sec += float(q.get("time", "0"))
        except (ValueError, TypeError):
            pass

    stats.template_counts = template_counts

    # Find the most repeated template
    if template_counts:
        template, count = max(template_counts.items(), key=lambda kv: kv[1])
        stats.most_repeated_template = template
        stats.most_repeated_count = count
        # N+1 decision: the same template repeating more than the threshold
        stats.n_plus_one_suspected = count > N_PLUS_ONE_THRESHOLD

    return stats
